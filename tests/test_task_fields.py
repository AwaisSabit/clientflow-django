"""Tests for task priority and assignee. A task's priority defaults
to medium, and an assignee must be a real user — posting a made-up
user id is rejected and saves nothing. Tasks are created under a
project, so the create page lives at that project's task list.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

GOOD_PASSWORD = "testpass123"


def make_user(username, **overrides):
    data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": GOOD_PASSWORD,
    }
    data.update(overrides)
    return User.objects.create_user(**data)


def make_client(owner, name="Sara Khan"):
    return Client.objects.create(
        owner=owner,
        name=name,
        email="sara@example.com",
        company="Khan Designs",
    )


def make_project(owner, client=None, name="Website redesign"):
    if client is None:
        client = make_client(owner)
    return Project.objects.create(owner=owner, client=client, name=name)


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


class TaskPriorityTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.project = make_project(self.user)
        self.create_url = reverse(
            "projects:task-create", args=[self.project.pk]
        )
        self.list_url = reverse(
            "projects:task-list", args=[self.project.pk]
        )

    def test_priority_defaults_to_medium(self):
        task = Task.objects.create(
            owner=self.user, project=self.project, title="Plain task"
        )
        self.assertEqual(task.priority, Task.Priority.MEDIUM)
        self.assertEqual(task.get_priority_display(), "Medium")

    def test_create_with_high_priority_saves_it(self):
        self.client.force_login(self.user)
        self.client.post(
            self.create_url,
            task_form_data(self.project, priority=Task.Priority.HIGH),
        )
        task = Task.objects.get(title="Design the home page")
        self.assertEqual(task.priority, Task.Priority.HIGH)

    def test_create_without_a_priority_saves_medium(self):
        self.client.force_login(self.user)
        self.client.post(
            self.create_url, task_form_data(self.project)
        )
        task = Task.objects.get(title="Design the home page")
        self.assertEqual(task.priority, Task.Priority.MEDIUM)

    def test_create_with_an_invalid_priority_saves_nothing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.create_url,
            task_form_data(self.project, priority="urgent"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 0)

    def test_update_changes_the_priority(self):
        task = Task.objects.create(
            owner=self.user, project=self.project, title="Plain task"
        )
        self.client.force_login(self.user)
        self.client.post(
            reverse("tasks:update", args=[task.pk]),
            task_form_data(
                self.project,
                title="Plain task",
                priority=Task.Priority.LOW,
            ),
        )
        task.refresh_from_db()
        self.assertEqual(task.priority, Task.Priority.LOW)

    def test_list_shows_the_priority(self):
        Task.objects.create(
            owner=self.user,
            project=self.project,
            title="Urgent fix",
            priority=Task.Priority.HIGH,
        )
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertContains(response, "High")


class TaskAssigneeTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.teammate = make_user("bilal")
        self.project = make_project(self.user)
        self.create_url = reverse(
            "projects:task-create", args=[self.project.pk]
        )

    def test_assignee_is_empty_by_default(self):
        task = Task.objects.create(
            owner=self.user, project=self.project, title="Plain task"
        )
        self.assertIsNone(task.assignee)

    def test_create_with_a_real_assignee_saves_it(self):
        self.client.force_login(self.user)
        self.client.post(
            self.create_url,
            task_form_data(
                self.project, assignee=str(self.teammate.pk)
            ),
        )
        task = Task.objects.get(title="Design the home page")
        self.assertEqual(task.assignee, self.teammate)

    def test_detail_shows_the_assignee(self):
        task = Task.objects.create(
            owner=self.user,
            project=self.project,
            title="Shared task",
            assignee=self.teammate,
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("tasks:detail", args=[task.pk])
        )
        self.assertContains(response, "bilal")

    def test_detail_without_an_assignee_shows_a_dash(self):
        task = Task.objects.create(
            owner=self.user, project=self.project, title="Solo task"
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("tasks:detail", args=[task.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "—")

    def test_create_with_a_made_up_assignee_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.create_url,
            task_form_data(self.project, assignee="999999"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 0)

    def test_update_clears_the_assignee(self):
        task = Task.objects.create(
            owner=self.user,
            project=self.project,
            title="Shared task",
            assignee=self.teammate,
        )
        self.client.force_login(self.user)
        self.client.post(
            reverse("tasks:update", args=[task.pk]),
            task_form_data(self.project, title="Shared task", assignee=""),
        )
        task.refresh_from_db()
        self.assertIsNone(task.assignee)

    def test_deleting_the_assignee_keeps_the_task(self):
        task = Task.objects.create(
            owner=self.user,
            project=self.project,
            title="Shared task",
            assignee=self.teammate,
        )
        self.teammate.delete()
        task.refresh_from_db()
        self.assertIsNone(task.assignee)
        self.assertEqual(Task.objects.count(), 1)
