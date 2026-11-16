"""Tests for the Task model and its list, create, detail, edit and
delete pages. Every test is written from the owner's point of view:
a signed-in user sees only their own tasks, and a task that belongs
to someone else answers with a 404. The client dropdown only ever
offers the signed-in user's own clients.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.tasks.models import Task

User = get_user_model()

TASK_LIST_URL = reverse("tasks:list")
TASK_CREATE_URL = reverse("tasks:create")
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


def make_task(owner, client, title="Design the home page", **overrides):
    data = {
        "description": "New layout for the client site.",
        "status": Task.Status.TODO,
        "due_date": date(2026, 11, 20),
    }
    data.update(overrides)
    return Task.objects.create(owner=owner, client=client, title=title, **data)


def task_form_data(client, **overrides):
    data = {
        "title": "Design the home page",
        "description": "New layout for the client site.",
        "client": str(client.pk),
        "status": Task.Status.TODO,
        "due_date": "2026-11-20",
    }
    data.update(overrides)
    return data


class TaskListTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_list_redirects_anonymous_users_to_login(self):
        response = self.client.get(TASK_LIST_URL)
        self.assertRedirects(response, f"{LOGIN_URL}?next={TASK_LIST_URL}")

    def test_empty_list_shows_the_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(TASK_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/list.html")
        self.assertContains(response, "No tasks yet")

    def test_list_shows_only_the_signed_in_users_tasks(self):
        make_task(self.user, self.client_obj, title="My task")
        other_client = make_client(self.other, name="Bilal Ltd")
        make_task(self.other, other_client, title="Someone else's task")
        self.client.force_login(self.user)
        response = self.client.get(TASK_LIST_URL)
        self.assertContains(response, "My task")
        self.assertNotContains(response, "Someone else's task")

    def test_list_is_ordered_by_due_date_with_undated_tasks_last(self):
        make_task(
            self.user,
            self.client_obj,
            title="Due later",
            due_date=date(2026, 11, 25),
        )
        make_task(
            self.user,
            self.client_obj,
            title="No due date",
            due_date=None,
        )
        make_task(
            self.user,
            self.client_obj,
            title="Due soonest",
            due_date=date(2026, 11, 17),
        )
        self.client.force_login(self.user)
        response = self.client.get(TASK_LIST_URL)
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(
            titles, ["Due soonest", "Due later", "No due date"]
        )

    def test_nav_shows_tasks_link_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(TASK_LIST_URL)
        self.assertContains(response, 'href="/tasks/"')
        self.assertContains(response, "Tasks")


class TaskCreateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_create_redirects_anonymous_users_to_login(self):
        response = self.client.get(TASK_CREATE_URL)
        self.assertRedirects(response, f"{LOGIN_URL}?next={TASK_CREATE_URL}")

    def test_create_saves_a_task_under_the_signed_in_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            TASK_CREATE_URL, task_form_data(self.client_obj)
        )
        task = Task.objects.get(title="Design the home page")
        self.assertEqual(task.owner, self.user)
        self.assertEqual(task.client, self.client_obj)
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertEqual(task.due_date, date(2026, 11, 20))
        self.assertRedirects(response, reverse("tasks:detail", args=[task.pk]))

    def test_create_without_a_title_saves_nothing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            TASK_CREATE_URL, task_form_data(self.client_obj, title="")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 0)

    def test_client_dropdown_only_lists_the_signed_in_users_clients(self):
        make_client(self.other, name="Bilal Ltd")
        self.client.force_login(self.user)
        response = self.client.get(TASK_CREATE_URL)
        choices = response.context["form"].fields["client"].queryset
        self.assertQuerySetEqual(
            choices, [self.client_obj], transform=lambda c: c
        )

    def test_create_with_another_users_client_is_rejected(self):
        other_client = make_client(self.other, name="Bilal Ltd")
        self.client.force_login(self.user)
        response = self.client.post(
            TASK_CREATE_URL, task_form_data(other_client)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 0)


class TaskDetailTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.task = make_task(self.user, self.client_obj)

    def test_detail_shows_the_task(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:detail", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/detail.html")
        self.assertContains(response, "Design the home page")
        self.assertContains(response, "New layout for the client site.")
        self.assertContains(response, "To do")
        self.assertContains(response, "20 November 2026")

    def test_detail_of_another_users_task_answers_404(self):
        other_client = make_client(self.other, name="Bilal Ltd")
        other_task = make_task(self.other, other_client, title="Secret task")
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:detail", args=[other_task.pk]))
        self.assertEqual(response.status_code, 404)


class TaskUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.task = make_task(self.user, self.client_obj)

    def test_update_saves_the_changes(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:update", args=[self.task.pk]),
            task_form_data(
                self.client_obj,
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
        other_client = make_client(self.other, name="Bilal Ltd")
        other_task = make_task(self.other, other_client, title="Secret task")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:update", args=[other_task.pk]),
            task_form_data(
                other_client, title="Changed by someone else"
            ),
        )
        self.assertEqual(response.status_code, 404)
        other_task.refresh_from_db()
        self.assertEqual(other_task.title, "Secret task")

    def test_update_with_another_users_client_is_rejected(self):
        other_client = make_client(self.other, name="Bilal Ltd")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:update", args=[self.task.pk]),
            task_form_data(other_client),
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.client, self.client_obj)


class TaskDeleteTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.task = make_task(self.user, self.client_obj)

    def test_delete_asks_for_confirmation_then_removes_the_task(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:delete", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/confirm_delete.html")
        response = self.client.post(
            reverse("tasks:delete", args=[self.task.pk])
        )
        self.assertRedirects(response, TASK_LIST_URL)
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_of_another_users_task_answers_404_and_changes_nothing(self):
        other_client = make_client(self.other, name="Bilal Ltd")
        other_task = make_task(self.other, other_client, title="Secret task")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tasks:delete", args=[other_task.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Task.objects.count(), 2)


class TaskModelTests(TestCase):
    def test_str_returns_the_title(self):
        user = make_user("awais")
        client_obj = make_client(user)
        task = make_task(user, client_obj)
        self.assertEqual(str(task), "Design the home page")

    def test_owner_can_reach_their_tasks(self):
        user = make_user("awais")
        client_obj = make_client(user)
        task = make_task(user, client_obj)
        self.assertIn(task, user.tasks.all())
        self.assertIn(task, client_obj.tasks.all())
