"""Tests for the dashboard page at /dashboard/.

The dashboard is a summary of the signed-in user's own work only: counts
of their clients, projects and tasks, their tasks split by status, their
overdue tasks soonest due first, and their newest items. Another user's
counts or items must never appear. The page needs a login, the nav shows
a Dashboard link when signed in, and the home page links to it.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.clients.models import Client
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

DASHBOARD_URL = reverse("dashboard:dashboard")
HOME_URL = reverse("home")
LOGIN_URL = reverse("accounts:login")
CLIENTS_LIST_URL = reverse("clients:list")
CLIENTS_CREATE_URL = reverse("clients:create")
PROJECTS_LIST_URL = reverse("projects:list")
PROJECTS_CREATE_URL = reverse("projects:create")

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


class DashboardAccessTests(TestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(DASHBOARD_URL)
        self.assertRedirects(
            response, f"{LOGIN_URL}?next={DASHBOARD_URL}"
        )

    def test_signed_in_user_sees_the_dashboard(self):
        user = make_user("awais")
        self.client.force_login(user)
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")
        self.assertContains(response, "Your dashboard")


class DashboardCountsTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client.force_login(self.user)
        self.client1 = make_client(self.user, name="Sara Khan")
        self.client2 = make_client(self.user, name="Omar Raza")
        self.project1 = make_project(
            self.user, self.client1, name="Website redesign"
        )
        self.project2 = make_project(
            self.user, self.client2, name="Shop app"
        )
        # The other user's items must never count towards this dashboard.
        other_client = make_client(self.other, name="Other Client")
        other_project = make_project(
            self.other, other_client, name="Other Project"
        )
        make_task(self.other, other_project, title="Other task")

    def test_counts_only_include_the_signed_in_users_own_items(self):
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["client_count"], 2)
        self.assertEqual(response.context["project_count"], 2)
        self.assertEqual(response.context["task_count"], 0)

        make_task(self.user, self.project1, title="Design the home page")
        make_task(self.user, self.project2, title="Build the cart")
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["client_count"], 2)
        self.assertEqual(response.context["project_count"], 2)
        self.assertEqual(response.context["task_count"], 2)

    def test_status_breakdown_counts_are_right(self):
        make_task(
            self.user, self.project1, title="To do task",
            status=Task.Status.TODO,
        )
        make_task(
            self.user, self.project1, title="Second to do task",
            status=Task.Status.TODO,
        )
        make_task(
            self.user, self.project2, title="Working task",
            status=Task.Status.IN_PROGRESS,
        )
        make_task(
            self.user, self.project2, title="Finished task",
            status=Task.Status.DONE,
        )
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["todo_count"], 2)
        self.assertEqual(response.context["in_progress_count"], 1)
        self.assertEqual(response.context["done_count"], 1)
        self.assertContains(response, "To do")
        self.assertContains(response, "In progress")
        self.assertContains(response, "Done")

    def test_empty_dashboard_shows_plain_empty_states(self):
        response = self.client.get(DASHBOARD_URL)
        self.assertContains(response, "No tasks yet")
        self.assertContains(response, "No overdue tasks")

    def test_empty_dashboard_with_no_items_shows_all_empty_states(self):
        fresh = make_user("fresh")
        self.client.force_login(fresh)
        response = self.client.get(DASHBOARD_URL)
        self.assertEqual(response.context["client_count"], 0)
        self.assertEqual(response.context["project_count"], 0)
        self.assertEqual(response.context["task_count"], 0)
        self.assertContains(response, "No clients yet")
        self.assertContains(response, "No projects yet")
        self.assertContains(response, "No tasks yet")


class DashboardOverdueTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client.force_login(self.user)
        self.project = make_project(self.user)
        self.today = timezone.localdate()
        self.yesterday = self.today - timedelta(days=1)
        self.five_days_ago = self.today - timedelta(days=5)
        self.tomorrow = self.today + timedelta(days=1)

    def test_overdue_list_only_has_past_due_unfinished_own_tasks(self):
        make_task(
            self.user, self.project, title="Oldest overdue",
            due_date=self.five_days_ago, status=Task.Status.TODO,
        )
        make_task(
            self.user, self.project, title="Newest overdue",
            due_date=self.yesterday, status=Task.Status.IN_PROGRESS,
        )
        make_task(
            self.user, self.project, title="Done but past due",
            due_date=self.five_days_ago, status=Task.Status.DONE,
        )
        make_task(
            self.user, self.project, title="Not due yet",
            due_date=self.tomorrow, status=Task.Status.TODO,
        )
        make_task(
            self.user, self.project, title="No due date",
            due_date=None, status=Task.Status.TODO,
        )
        other_project = make_project(self.other)
        make_task(
            self.other, other_project, title="Other overdue task",
            due_date=self.five_days_ago, status=Task.Status.TODO,
        )

        response = self.client.get(DASHBOARD_URL)
        overdue = list(response.context["overdue_tasks"])
        self.assertEqual(
            [task.title for task in overdue],
            ["Oldest overdue", "Newest overdue"],
        )
        # The overdue section itself must not list the finished, not-yet-due
        # or dateless tasks — even though the recent-tasks list below
        # rightly shows them as the user's newest tasks.
        overdue_section = (
            response.content.decode()
            .split("Overdue tasks")[1]
            .split("Recent clients")[0]
        )
        self.assertIn("Oldest overdue", overdue_section)
        self.assertIn("Newest overdue", overdue_section)
        self.assertNotIn("Done but past due", overdue_section)
        self.assertNotIn("Not due yet", overdue_section)
        self.assertNotIn("No due date", overdue_section)
        self.assertNotIn("Other overdue task", overdue_section)
        # The other user's overdue task must not appear anywhere.
        self.assertNotContains(response, "Other overdue task")

    def test_overdue_tasks_link_to_their_detail_pages(self):
        task = make_task(
            self.user, self.project, title="Late task",
            due_date=self.yesterday, status=Task.Status.TODO,
        )
        response = self.client.get(DASHBOARD_URL)
        self.assertContains(
            response, reverse("tasks:detail", args=[task.pk])
        )


class DashboardRecentTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client.force_login(self.user)

    def test_recent_lists_show_the_users_newest_items_only(self):
        clients = [
            make_client(self.user, name=f"Client {number}")
            for number in range(6)
        ]
        projects = [
            make_project(self.user, clients[0], name=f"Project {number}")
            for number in range(6)
        ]
        tasks = [
            make_task(self.user, projects[number], title=f"Task {number}")
            for number in range(6)
        ]
        make_client(self.other, name="Other Client")
        other_project = make_project(self.other, name="Other Project")
        make_task(self.other, other_project, title="Other Task")

        response = self.client.get(DASHBOARD_URL)
        recent_clients = list(response.context["recent_clients"])
        recent_projects = list(response.context["recent_projects"])
        recent_tasks = list(response.context["recent_tasks"])
        # Newest first, only the newest five of each.
        self.assertEqual(recent_clients, list(reversed(clients[1:])))
        self.assertEqual(recent_projects, list(reversed(projects[1:])))
        self.assertEqual(recent_tasks, list(reversed(tasks[1:])))
        self.assertNotContains(response, "Client 0")
        self.assertNotContains(response, "Project 0")
        self.assertNotContains(response, "Task 0")
        self.assertNotContains(response, "Other Client")
        self.assertNotContains(response, "Other Project")
        self.assertNotContains(response, "Other Task")


class DashboardLinksTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.client.force_login(self.user)
        self.project = make_project(self.user)

    def test_nav_shows_dashboard_when_signed_in(self):
        response = self.client.get(DASHBOARD_URL)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, f'href="{DASHBOARD_URL}"')

    def test_nav_hides_dashboard_when_signed_out(self):
        self.client.logout()
        response = self.client.get(HOME_URL)
        self.assertNotContains(response, "Dashboard")

    def test_home_page_links_to_the_dashboard_when_signed_in(self):
        response = self.client.get(HOME_URL)
        self.assertContains(response, "Open your dashboard")
        self.assertContains(response, f'href="{DASHBOARD_URL}"')

    def test_home_page_has_no_dashboard_link_when_signed_out(self):
        self.client.logout()
        response = self.client.get(HOME_URL)
        self.assertNotContains(response, "Open your dashboard")

    def test_dashboard_quick_links_work(self):
        response = self.client.get(DASHBOARD_URL)
        self.assertContains(response, f'href="{CLIENTS_CREATE_URL}"')
        self.assertContains(response, f'href="{PROJECTS_CREATE_URL}"')
        self.assertContains(response, f'href="{CLIENTS_LIST_URL}"')
        self.assertContains(response, f'href="{PROJECTS_LIST_URL}"')
        for url in (
            CLIENTS_CREATE_URL,
            PROJECTS_CREATE_URL,
            CLIENTS_LIST_URL,
            PROJECTS_LIST_URL,
        ):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_dashboard_links_to_recent_items(self):
        client = make_client(self.user, name="Sara Khan")
        task = make_task(self.user, self.project, title="Design the home page")
        response = self.client.get(DASHBOARD_URL)
        self.assertContains(
            response, reverse("clients:detail", args=[client.pk])
        )
        self.assertContains(
            response, reverse("projects:detail", args=[self.project.pk])
        )
        self.assertContains(
            response, reverse("tasks:detail", args=[task.pk])
        )
        for url in (
            reverse("clients:detail", args=[client.pk]),
            reverse("projects:detail", args=[self.project.pk]),
            reverse("tasks:detail", args=[task.pk]),
        ):
            self.assertEqual(self.client.get(url).status_code, 200)
