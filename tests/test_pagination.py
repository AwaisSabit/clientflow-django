"""Tests for pagination on the invoice, project and task lists.

Every list shows 10 items per page. An out-of-range page shows the
last page instead of an error, and a page that is not a number shows
the first page. The invoice list keeps its status filter in the page
links, and pagination never shows another user's items.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceLineItem
from apps.clients.models import Client
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

INVOICE_LIST_URL = reverse("billing:list")
PROJECT_LIST_URL = reverse("projects:list")
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


def make_invoice(owner, client, project=None, **overrides):
    data = {
        "status": Invoice.Status.DRAFT,
        "issue_date": date.today(),
        "due_date": date.today() + timedelta(days=10),
    }
    data.update(overrides)
    return Invoice.objects.create(
        owner=owner, client=client, project=project, **data
    )


def make_task(owner, project, title="Design the home page", **overrides):
    data = {
        "description": "New layout for the client site.",
        "status": Task.Status.TODO,
    }
    data.update(overrides)
    return Task.objects.create(owner=owner, project=project, title=title, **data)


class InvoiceListPaginationTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)
        # Twelve invoices with distinct created times, so the
        # newest-first order is exact, not a tie.
        self.invoices = []
        for number in range(12):
            invoice = make_invoice(self.user, self.client_obj, self.project)
            Invoice.objects.filter(pk=invoice.pk).update(
                created=timezone.now() - timedelta(days=number)
            )
            self.invoices.append(invoice)

    def test_first_page_shows_ten_newest_invoices(self):
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_LIST_URL)
        self.assertEqual(response.status_code, 200)
        page = response.context["invoices"]
        self.assertEqual(len(page), 10)
        self.assertEqual(page.number, 1)
        self.assertEqual(response.context["total_count"], 12)
        self.assertContains(response, "12 invoices")
        # Newest first: the first ten created, oldest two left out.
        self.assertEqual(
            [invoice.pk for invoice in page],
            [invoice.pk for invoice in self.invoices[:10]],
        )

    def test_second_page_shows_the_remaining_two(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{INVOICE_LIST_URL}?page=2")
        page = response.context["invoices"]
        self.assertEqual(len(page), 2)
        self.assertEqual(page.number, 2)
        self.assertEqual(
            [invoice.pk for invoice in page],
            [invoice.pk for invoice in self.invoices[10:]],
        )

    def test_out_of_range_page_shows_the_last_page(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{INVOICE_LIST_URL}?page=99")
        page = response.context["invoices"]
        self.assertEqual(page.number, 2)
        self.assertEqual(len(page), 2)

    def test_a_page_that_is_not_a_number_shows_the_first_page(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{INVOICE_LIST_URL}?page=abc")
        self.assertEqual(response.context["invoices"].number, 1)

    def test_status_filter_and_pagination_work_together(self):
        for invoice in self.invoices:
            invoice.status = Invoice.Status.PAID
            invoice.save()
        make_invoice(
            self.user, self.client_obj, self.project,
            status=Invoice.Status.DRAFT,
        )
        self.client.force_login(self.user)
        response = self.client.get(f"{INVOICE_LIST_URL}?status=paid")
        page = response.context["invoices"]
        self.assertEqual(len(page), 10)
        self.assertEqual(response.context["total_count"], 12)
        self.assertContains(response, "12 invoices")
        # The page links keep the status filter.
        self.assertContains(response, "status=paid")
        self.assertContains(response, "page=2")
        response = self.client.get(
            f"{INVOICE_LIST_URL}?status=paid&page=2"
        )
        self.assertEqual(len(response.context["invoices"]), 2)
        self.assertContains(response, "status=paid")

    def test_pagination_never_shows_another_users_invoices(self):
        other_client = make_client(self.other, name="Omar Farooq")
        for _ in range(12):
            make_invoice(self.other, other_client)
        self.client.force_login(self.user)
        response = self.client.get(f"{INVOICE_LIST_URL}?page=2")
        self.assertEqual(response.context["total_count"], 12)
        self.assertEqual(len(response.context["invoices"]), 2)
        self.assertNotContains(response, "Omar Farooq")


class ProjectListPaginationTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.projects = [
            make_project(
                self.user, self.client_obj, name=f"Project {number:02d}"
            )
            for number in range(12)
        ]

    def test_first_page_shows_ten_projects_in_name_order(self):
        self.client.force_login(self.user)
        response = self.client.get(PROJECT_LIST_URL)
        page = response.context["projects"]
        self.assertEqual(len(page), 10)
        self.assertEqual(page.number, 1)
        self.assertEqual(response.context["total_count"], 12)
        self.assertContains(response, "12 projects")
        self.assertEqual(
            [project.name for project in page],
            [f"Project {number:02d}" for number in range(10)],
        )

    def test_second_page_shows_the_remaining_two(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{PROJECT_LIST_URL}?page=2")
        page = response.context["projects"]
        self.assertEqual(len(page), 2)
        self.assertEqual(
            [project.name for project in page],
            ["Project 10", "Project 11"],
        )

    def test_out_of_range_page_shows_the_last_page(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{PROJECT_LIST_URL}?page=99")
        self.assertEqual(response.context["projects"].number, 2)

    def test_empty_list_still_shows_the_empty_state(self):
        fresh = make_user("fresh")
        self.client.force_login(fresh)
        response = self.client.get(PROJECT_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No projects yet")

    def test_pagination_never_shows_another_users_projects(self):
        make_project(self.other, name="Secret project")
        self.client.force_login(self.user)
        response = self.client.get(f"{PROJECT_LIST_URL}?page=2")
        self.assertEqual(response.context["total_count"], 12)
        self.assertNotContains(response, "Secret project")


class TaskListPaginationTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.project = make_project(self.user)
        self.list_url = reverse(
            "projects:task-list", args=[self.project.pk]
        )
        # Twelve tasks with distinct due dates, so the soonest-first
        # order is exact.
        self.tasks = [
            make_task(
                self.user, self.project, title=f"Task {number:02d}",
                due_date=date(2026, 12, 1) + timedelta(days=number),
            )
            for number in range(12)
        ]

    def test_first_page_shows_ten_tasks_soonest_due_first(self):
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        page = response.context["tasks"]
        self.assertEqual(len(page), 10)
        self.assertEqual(page.number, 1)
        self.assertEqual(response.context["total_count"], 12)
        self.assertContains(response, "12 tasks")
        self.assertEqual(
            [task.title for task in page],
            [f"Task {number:02d}" for number in range(10)],
        )

    def test_second_page_shows_the_remaining_two(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{self.list_url}?page=2")
        page = response.context["tasks"]
        self.assertEqual(len(page), 2)
        self.assertEqual(
            [task.title for task in page], ["Task 10", "Task 11"]
        )

    def test_out_of_range_page_shows_the_last_page(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{self.list_url}?page=99")
        self.assertEqual(response.context["tasks"].number, 2)

    def test_empty_list_still_shows_the_empty_state(self):
        empty_project = make_project(self.user, name="Empty project")
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("projects:task-list", args=[empty_project.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks for this project yet")

    def test_pagination_never_shows_another_users_tasks(self):
        other_project = make_project(self.other, name="Secret project")
        make_task(
            self.other, other_project, title="Someone else's task"
        )
        self.client.force_login(self.user)
        response = self.client.get(f"{self.list_url}?page=2")
        self.assertEqual(response.context["total_count"], 12)
        self.assertNotContains(response, "Someone else's task")
