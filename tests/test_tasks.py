"""Tests for the Task model and its list, create, detail, edit and
delete pages. Every test is written from the owner's point of view:
a signed-in user sees only their own tasks, and a task that belongs
to someone else answers with a 404. Tasks belong to a project, and
the list and creation live under that project; the project dropdown
only ever offers the signed-in user's own projects.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

LOGIN_URL = reverse("accounts:login")

GOOD_PASSWORD = "testpass123"


def make_user(username, **overrides):
    data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": GOOD_PASSWORD,
    }
    data.update(overrides)
    return User.objects.create_user(**data)


def make_client(owner, name="Sara Khan", **overrides):
    data = {
        "name": name,
        "email": "sara@example.com",
        "company": "Khan Designs",
    }
    data.update(overrides)
    return Client.objects.create(owner=owner, **data)


def make_project(owner, client=None, name="Website redesign", **overrides):
    if client is None:
        client = make_client(owner)
    data = {"name": name, "description": "New site for the client."}
    data.update(overrides)
    return Project.objects.create(owner=owner, client=client, **data)


def make_task(owner, project, title="Design the home page", **overrides):
    data = {
        "description": "New layout for the client site.",
        "status": Task.Status.TODO,
        "due_date": date(2026, 11, 20),
    }
    data.update(overrides)
    return Task.objects.create(owner=owner, project=project, title=title, **data)


def task_form_data(project, **overrides):
    data = {
        "title": "Design the home page",
        "description": "New layout for the client site.",
        "project": str(project.pk),
        "status": Task.Status.TODO,
        "due_date": "2026-11-20",
    }
    data.update(overrides)
    return data


class TaskListTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.project = make_project(self.user)
        self.list_url = reverse(
            "projects:task-list", args=[self.project.pk]
        )

    def test_list_redirects_anonymous_users_to_login(self):
        response = self.client.get(self.list_url)
        self.assertRedirects(response, f"{LOGIN_URL}?next={self.list_url}")

    def test_list_of_another_users_project_answers_404(self):
        other_project = make_project(self.other, name="Secret project")
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("projects:task-list", args=[other_project.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_empty_list_shows_the_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/list.html")
        self.assertContains(response, "No tasks for this project yet")

    def test_list_shows_only_the_signed_in_users_tasks(self):
        make_task(self.user, self.project, title="My task")
        other_project = make_project(self.other, name="Secret project")
        make_task(self.other, other_project, title="Someone else's task")
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertContains(response, "My task")
        self.assertNotContains(response, "Someone else's task")

    def test_list_is_ordered_by_due_date_with_undated_tasks_last(self):
        make_task(
            self.user,
            self.project,
            title="Due later",
            due_date=date(2026, 11, 25),
        )
        make_task(
            self.user,
            self.project,
            title="No due date",
            due_date=None,
        )
        make_task(
            self.user,
            self.project,
            title="Due soonest",
            due_date=date(2026, 11, 17),
        )
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(
            titles, ["Due soonest", "Due later", "No due date"]
        )

    def test_task_is_reachable_from_its_project(self):
        task = make_task(self.user, self.project)
        self.assertIn(task, self.project.tasks.all())
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("projects:detail", args=[self.project.pk])
        )
        self.assertContains(response, "Design the home page")
        self.assertContains(
            response, reverse("tasks:detail", args=[task.pk])
        )

    def test_nav_shows_projects_link_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertContains(response, 'href="/projects/"')
        self.assertContains(response, "Projects")


class TaskCreateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.project = make_project(self.user)
        self.create_url = reverse(
            "projects:task-create", args=[self.project.pk]
        )

    def test_create_redirects_anonymous_users_to_login(self):
        response = self.client.get(self.create_url)
        self.assertRedirects(
            response, f"{LOGIN_URL}?next={self.create_url}"
        )

    def test_create_under_another_users_project_answers_404(self):
        other_project = make_project(self.other, name="Secret project")
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("projects:task-create", args=[other_project.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_create_saves_a_task_under_the_signed_in_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.create_url, task_form_data(self.project)
        )
        task = Task.objects.get(title="Design the home page")
        self.assertEqual(task.owner, self.user)
        self.assertEqual(task.project, self.project)
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertEqual(task.due_date, date(2026, 11, 20))
        self.assertRedirects(response, reverse("tasks:detail", args=[task.pk]))

    def test_create_uses_the_project_from_the_url(self):
        other_project = make_project(self.user, name="Second project")
        self.client.force_login(self.user)
        response = self.client.post(
            self.create_url, task_form_data(other_project)
        )
        task = Task.objects.get(title="Design the home page")
        self.assertEqual(task.project, self.project)
        self.assertRedirects(response, reverse("tasks:detail", args=[task.pk]))

    def test_create_without_a_title_saves_nothing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.create_url, task_form_data(self.project, title="")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 0)

    def test_project_dropdown_only_lists_the_signed_in_users_projects(self):
        make_project(self.other, name="Secret project")
        self.client.force_login(self.user)
        response = self.client.get(self.create_url)
        choices = response.context["form"].fields["project"].queryset
        self.assertQuerySetEqual(
            choices, [self.project], transform=lambda p: p
        )

    def test_create_with_another_users_project_is_rejected(self):
        other_project = make_project(self.other, name="Secret project")
        self.client.force_login(self.user)
        response = self.client.post(
            self.create_url, task_form_data(other_project)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 0)


class TaskDetailTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.project = make_project(self.user)
        self.task = make_task(self.user, self.project)

    def test_detail_shows_the_task_and_its_project(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:detail", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/detail.html")
        self.assertContains(response, "Design the home page")
        self.assertContains(response, "New layout for the client site.")
        self.assertContains(response, "To do")
        self.assertContains(response, "20 November 2026")
        self.assertContains(response, "Website redesign")

    def test_detail_of_another_users_task_answers_404(self):
        other_project = make_project(self.other, name="Secret project")
        other_task = make_task(self.other, other_project, title="Secret task")
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:detail", args=[other_task.pk]))
        self.assertEqual(response.status_code, 404)


class TaskUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.project = make_project(self.user)
        self.task = make_task(self.user, self.project)

    def test_update_saves_the_changes(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:update", args=[self.task.pk]),
            task_form_data(
                self.project,
                title="Redesign the home page",
                status=Task.Status.IN_PROGRESS,
            ),
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Redesign the home page")
        self.assertEqual(self.task.status, Task.Status.IN_PROGRESS)
        self.assertRedirects(
            response, reverse("tasks:detail", args=[self.task.pk])
        )

    def test_update_of_another_users_task_answers_404_and_changes_nothing(self):
        other_project = make_project(self.other, name="Secret project")
        other_task = make_task(self.other, other_project, title="Secret task")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:update", args=[other_task.pk]),
            task_form_data(
                other_project, title="Changed by someone else"
            ),
        )
        self.assertEqual(response.status_code, 404)
        other_task.refresh_from_db()
        self.assertEqual(other_task.title, "Secret task")

    def test_update_with_another_users_project_is_rejected(self):
        other_project = make_project(self.other, name="Secret project")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:update", args=[self.task.pk]),
            task_form_data(other_project),
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.project, self.project)


class TaskDeleteTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.project = make_project(self.user)
        self.task = make_task(self.user, self.project)

    def test_delete_asks_for_confirmation_then_removes_the_task(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:delete", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/confirm_delete.html")
        response = self.client.post(
            reverse("tasks:delete", args=[self.task.pk])
        )
        self.assertRedirects(
            response,
            reverse("projects:task-list", args=[self.project.pk]),
        )
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_of_another_users_task_answers_404_and_changes_nothing(self):
        other_project = make_project(self.other, name="Secret project")
        other_task = make_task(self.other, other_project, title="Secret task")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:delete", args=[other_task.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Task.objects.count(), 2)


class TaskModelTests(TestCase):
    def test_str_returns_the_title(self):
        user = make_user("awais")
        project = make_project(user)
        task = make_task(user, project)
        self.assertEqual(str(task), "Design the home page")

    def test_owner_and_project_can_reach_their_tasks(self):
        user = make_user("awais")
        project = make_project(user)
        task = make_task(user, project)
        self.assertIn(task, user.tasks.all())
        self.assertIn(task, project.tasks.all())
