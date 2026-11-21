"""Tests for task state: status changes through the edit page,
assignee changes, and dashboard edge cases when there are many
tasks. The edit page sets the status directly (it does not enforce
the one-click invoice-style transitions), so every status move is
allowed there; the dashboard must still count and list them right.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.clients.models import Client
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

DASHBOARD_URL = reverse("dashboard:dashboard")

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
    }
    data.update(overrides)
    return Task.objects.create(owner=owner, project=project, title=title, **data)


def task_form_data(project, **overrides):
    data = {
        "title": "Design the home page",
        "description": "New layout for the client site.",
        "project": str(project.pk),
        "status": Task.Status.TODO,
        "priority": Task.Priority.MEDIUM,
        "assignee": "",
        "due_date": "",
    }
    data.update(overrides)
    return data


class TaskStatusTransitionTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.project = make_project(self.user)
        self.task = make_task(self.user, self.project)
        self.update_url = reverse("tasks:update", args=[self.task.pk])
        self.client.force_login(self.user)

    def _move_task(self, status):
        response = self.client.post(
            self.update_url,
            task_form_data(self.project, status=status),
        )
        self.assertRedirects(
            response, reverse("tasks:detail", args=[self.task.pk])
        )
        self.task.refresh_from_db()
        return self.task.status

    def test_task_can_move_from_to_do_to_in_progress(self):
        self.assertEqual(
            self._move_task(Task.Status.IN_PROGRESS),
            Task.Status.IN_PROGRESS,
        )

    def test_task_can_move_from_in_progress_to_done(self):
        self.task.status = Task.Status.IN_PROGRESS
        self.task.save()
        self.assertEqual(
            self._move_task(Task.Status.DONE), Task.Status.DONE
        )

    def test_done_task_can_be_reopened_to_to_do(self):
        self.task.status = Task.Status.DONE
        self.task.save()
        self.assertEqual(
            self._move_task(Task.Status.TODO), Task.Status.TODO
        )

    def test_done_task_can_go_back_to_in_progress(self):
        self.task.status = Task.Status.DONE
        self.task.save()
        self.assertEqual(
            self._move_task(Task.Status.IN_PROGRESS),
            Task.Status.IN_PROGRESS,
        )

    def test_task_can_move_straight_from_to_do_to_done(self):
        self.assertEqual(
            self._move_task(Task.Status.DONE), Task.Status.DONE
        )

    def test_an_invalid_status_is_rejected_and_changes_nothing(self):
        response = self.client.post(
            self.update_url,
            task_form_data(self.project, status="almost_done"),
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.TODO)

    def test_changing_status_keeps_priority_and_assignee(self):
        teammate = make_user("teammate")
        self.task.priority = Task.Priority.HIGH
        self.task.assignee = teammate
        self.task.save()
        # The edit form posts every field, so the current priority
        # and assignee go along with the new status and must survive.
        response = self.client.post(
            self.update_url,
            task_form_data(
                self.project,
                status=Task.Status.IN_PROGRESS,
                priority=Task.Priority.HIGH,
                assignee=str(teammate.pk),
            ),
        )
        self.assertRedirects(
            response, reverse("tasks:detail", args=[self.task.pk])
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.IN_PROGRESS)
        self.assertEqual(self.task.priority, Task.Priority.HIGH)
        self.assertEqual(self.task.assignee, teammate)


class TaskAssigneeChangeTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.teammate = make_user("teammate")
        self.other_teammate = make_user("other-teammate")
        self.project = make_project(self.user)
        self.task = make_task(self.user, self.project)
        self.update_url = reverse("tasks:update", args=[self.task.pk])
        self.client.force_login(self.user)

    def test_assigning_an_unassigned_task_shows_the_assignee(self):
        response = self.client.post(
            self.update_url,
            task_form_data(
                self.project, assignee=str(self.teammate.pk)
            ),
        )
        self.assertRedirects(
            response, reverse("tasks:detail", args=[self.task.pk])
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.assignee, self.teammate)
        detail = self.client.get(
            reverse("tasks:detail", args=[self.task.pk])
        )
        self.assertContains(detail, "teammate")

    def test_reassigning_a_task_moves_it_to_the_new_assignee(self):
        self.task.assignee = self.teammate
        self.task.save()
        self.client.post(
            self.update_url,
            task_form_data(
                self.project, assignee=str(self.other_teammate.pk)
            ),
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.assignee, self.other_teammate)

    def test_assigning_a_made_up_user_is_rejected(self):
        response = self.client.post(
            self.update_url,
            task_form_data(self.project, assignee="999999"),
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.assignee)


class DashboardEdgeCaseTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.project = make_project(self.user)
        self.today = timezone.localdate()
        self.client.force_login(self.user)

    def test_task_due_today_is_not_overdue(self):
        make_task(
            self.user, self.project, title="Due today",
            due_date=self.today, status=Task.Status.TODO,
        )
        response = self.client.get(DASHBOARD_URL)
        overdue = list(response.context["overdue_tasks"])
        self.assertEqual(overdue, [])
        self.assertContains(response, "No overdue tasks")

    def test_overdue_list_shows_every_overdue_task_not_just_five(self):
        for number in range(7):
            make_task(
                self.user, self.project, title=f"Late task {number}",
                due_date=self.today - timedelta(days=number + 1),
                status=Task.Status.TODO,
            )
        response = self.client.get(DASHBOARD_URL)
        overdue = list(response.context["overdue_tasks"])
        self.assertEqual(len(overdue), 7)

    def test_counts_are_right_with_twelve_tasks(self):
        statuses = (
            [Task.Status.TODO] * 5
            + [Task.Status.IN_PROGRESS] * 4
            + [Task.Status.DONE] * 3
        )
        for number, status in enumerate(statuses):
            make_task(
                self.user, self.project, title=f"Task {number}",
                status=status,
            )
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["task_count"], 12)
        self.assertEqual(response.context["todo_count"], 5)
        self.assertEqual(response.context["in_progress_count"], 4)
        self.assertEqual(response.context["done_count"], 3)

    def test_recent_lists_still_show_only_five_with_twelve_tasks(self):
        clients = [
            make_client(self.user, name=f"Client {number}")
            for number in range(12)
        ]
        for number in range(12):
            make_task(
                self.user, self.project, title=f"Task {number}"
            )
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["task_count"], 12)
        self.assertEqual(len(response.context["recent_clients"]), 5)
        self.assertEqual(len(response.context["recent_tasks"]), 5)
        self.assertNotContains(response, "Client 0")
        self.assertNotContains(response, "Task 0")

    def test_marking_tasks_done_moves_them_between_counts(self):
        first = make_task(
            self.user, self.project, title="First task",
            status=Task.Status.TODO,
        )
        make_task(
            self.user, self.project, title="Second task",
            status=Task.Status.TODO,
        )
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["todo_count"], 2)
        self.assertEqual(response.context["done_count"], 0)
        first.status = Task.Status.DONE
        first.save()
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["todo_count"], 1)
        self.assertEqual(response.context["done_count"], 1)
