"""Tests that the list, detail and dashboard pages load their
related records in a fixed number of queries, no matter how many
rows there are.

Each test loads the same page twice — once with one related row and
once with twelve — and the query count must be identical. A page
that asked the database once per row would grow with the rows; these
pages do not. A few pages also pin the exact count, so a future
regression that adds a query per row (or per page) fails loudly.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceLineItem
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


def make_item(invoice, description="Design work", quantity="1",
              unit_price="10.00"):
    return InvoiceLineItem.objects.create(
        invoice=invoice,
        description=description,
        quantity=Decimal(quantity),
        unit_price=Decimal(unit_price),
    )


def make_task(owner, project, title="Design the home page", **overrides):
    data = {
        "description": "New layout for the client site.",
        "status": Task.Status.TODO,
    }
    data.update(overrides)
    return Task.objects.create(owner=owner, project=project, title=title, **data)


def query_count(test_client, url):
    """How many queries one GET of `url` makes."""
    with CaptureQueriesContext(connection) as context:
        response = test_client.get(url)
    assert response.status_code == 200, (url, response.status_code)
    return len(context)


class QueryOptimisationTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.teammate = make_user("teammate")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)
        self.client.force_login(self.user)

    def test_invoice_list_query_count_does_not_grow(self):
        make_invoice(self.user, self.client_obj, self.project)
        one = query_count(self.client, reverse("billing:list"))
        for _ in range(11):
            make_invoice(self.user, self.client_obj, self.project)
        many = query_count(self.client, reverse("billing:list"))
        self.assertEqual(one, many)

    def test_invoice_list_loads_in_four_queries(self):
        make_invoice(self.user, self.client_obj, self.project)
        self.assertNumQueries(
            4, lambda: self.client.get(reverse("billing:list"))
        )

    def test_invoice_export_query_count_does_not_grow(self):
        invoice = make_invoice(self.user, self.client_obj, self.project)
        make_item(invoice)
        one = query_count(self.client, reverse("billing:export"))
        for _ in range(11):
            extra = make_invoice(
                self.user, self.client_obj, self.project
            )
            make_item(extra)
            make_item(extra, description="Hosting")
        many = query_count(self.client, reverse("billing:export"))
        self.assertEqual(one, many)

    def test_invoice_export_loads_in_four_queries(self):
        invoice = make_invoice(self.user, self.client_obj, self.project)
        make_item(invoice)
        self.assertNumQueries(
            4, lambda: self.client.get(reverse("billing:export"))
        )

    def test_invoice_detail_query_count_does_not_grow_with_line_items(self):
        invoice = make_invoice(self.user, self.client_obj, self.project)
        make_item(invoice)
        one = query_count(
            self.client,
            reverse("billing:detail", args=[invoice.pk]),
        )
        for number in range(11):
            make_item(invoice, description=f"Extra work {number}")
        many = query_count(
            self.client,
            reverse("billing:detail", args=[invoice.pk]),
        )
        self.assertEqual(one, many)

    def test_invoice_detail_loads_in_four_queries(self):
        invoice = make_invoice(self.user, self.client_obj, self.project)
        make_item(invoice)
        self.assertNumQueries(
            4,
            lambda: self.client.get(
                reverse("billing:detail", args=[invoice.pk])
            ),
        )

    def test_project_list_query_count_does_not_grow(self):
        make_project(self.user, self.client_obj, name="Project 00")
        one = query_count(self.client, reverse("projects:list"))
        for number in range(1, 12):
            make_project(
                self.user, self.client_obj, name=f"Project {number:02d}"
            )
        many = query_count(self.client, reverse("projects:list"))
        self.assertEqual(one, many)

    def test_project_detail_query_count_does_not_grow_with_tasks(self):
        make_task(self.user, self.project, title="Task 00")
        one = query_count(
            self.client,
            reverse("projects:detail", args=[self.project.pk]),
        )
        for number in range(1, 12):
            make_task(
                self.user, self.project, title=f"Task {number:02d}"
            )
        many = query_count(
            self.client,
            reverse("projects:detail", args=[self.project.pk]),
        )
        self.assertEqual(one, many)

    def test_task_list_query_count_does_not_grow_with_assignees(self):
        make_task(
            self.user, self.project, title="Task 00",
            assignee=self.teammate,
        )
        one = query_count(
            self.client,
            reverse("projects:task-list", args=[self.project.pk]),
        )
        for number in range(1, 12):
            make_task(
                self.user, self.project, title=f"Task {number:02d}",
                assignee=self.teammate,
            )
        many = query_count(
            self.client,
            reverse("projects:task-list", args=[self.project.pk]),
        )
        self.assertEqual(one, many)

    def test_client_detail_query_count_does_not_grow_with_projects(self):
        make_project(self.user, self.client_obj, name="Project 00")
        one = query_count(
            self.client,
            reverse("clients:detail", args=[self.client_obj.pk]),
        )
        for number in range(1, 12):
            make_project(
                self.user, self.client_obj, name=f"Project {number:02d}"
            )
        many = query_count(
            self.client,
            reverse("clients:detail", args=[self.client_obj.pk]),
        )
        self.assertEqual(one, many)

    def test_dashboard_query_count_does_not_grow_with_tasks(self):
        make_task(
            self.user, self.project, title="Task 00",
            due_date=timezone.localdate() - timedelta(days=1),
        )
        one = query_count(self.client, reverse("dashboard:dashboard"))
        for number in range(1, 12):
            make_task(
                self.user, self.project, title=f"Task {number:02d}",
                status=(
                    Task.Status.DONE
                    if number % 2
                    else Task.Status.IN_PROGRESS
                ),
                due_date=timezone.localdate() - timedelta(days=number),
            )
        many = query_count(self.client, reverse("dashboard:dashboard"))
        self.assertEqual(one, many)

    def test_dashboard_loads_in_nine_queries(self):
        make_task(self.user, self.project, title="Task 00")
        self.assertNumQueries(
            9, lambda: self.client.get(reverse("dashboard:dashboard"))
        )
