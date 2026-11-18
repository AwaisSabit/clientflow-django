"""Tests for the Invoice and InvoiceLineItem models and the invoice
list, create and detail pages. Every test is written from the owner's
point of view: a signed-in user sees only their own invoices, and an
invoice that belongs to someone else answers with a 404. The client
and project dropdowns only ever offer the signed-in user's own
clients and projects.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.billing.models import Invoice, InvoiceLineItem
from apps.clients.models import Client
from apps.projects.models import Project

User = get_user_model()

INVOICE_LIST_URL = reverse("billing:list")
INVOICE_CREATE_URL = reverse("billing:create")
LOGIN_URL = reverse("accounts:login")

GOOD_PASSWORD = "testpass123"
TODAY = date.today()
PAST = TODAY - timedelta(days=10)
FUTURE = TODAY + timedelta(days=10)


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


def make_project(owner, client, name="Website redesign", **overrides):
    data = {"description": "New site for the client."}
    data.update(overrides)
    return Project.objects.create(
        owner=owner, client=client, name=name, **data
    )


def make_invoice(owner, client, project=None, **overrides):
    data = {
        "status": Invoice.Status.DRAFT,
        "issue_date": TODAY,
        "due_date": FUTURE,
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


def invoice_form_data(client, project=None, **overrides):
    data = {
        "client": str(client.pk),
        "project": str(project.pk) if project else "",
        "status": Invoice.Status.DRAFT,
        "issue_date": TODAY.isoformat(),
        "due_date": "",
    }
    data.update(overrides)
    return data


def item_formset_data(prefix, items):
    """Management form plus one row per item dict."""
    data = {
        f"{prefix}-TOTAL_FORMS": str(len(items)),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "1",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }
    for i, item in enumerate(items):
        data[f"{prefix}-{i}-description"] = item.get("description", "")
        data[f"{prefix}-{i}-quantity"] = item.get("quantity", "")
        data[f"{prefix}-{i}-unit_price"] = item.get("unit_price", "")
    return data


class InvoiceListTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_list_redirects_anonymous_users_to_login(self):
        response = self.client.get(INVOICE_LIST_URL)
        self.assertRedirects(response, f"{LOGIN_URL}?next={INVOICE_LIST_URL}")

    def test_empty_list_shows_the_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No invoices yet")

    def test_list_shows_only_the_signed_in_users_invoices(self):
        mine = make_invoice(self.user, self.client_obj)
        other_client = make_client(self.other, name="Omar Farooq")
        make_invoice(self.other, other_client)
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_LIST_URL)
        self.assertContains(response, mine.number)
        self.assertContains(response, "Draft")
        # The other user's invoice must not appear at all: only one
        # invoice is listed, and it is mine.
        invoices = list(response.context["invoices"])
        self.assertEqual(invoices, [mine])

    def test_nav_shows_invoices_link_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_LIST_URL)
        self.assertContains(response, reverse("billing:list"))
        self.assertContains(response, "Invoices")


class InvoiceCreateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)

    def _post_invoice(self, form_data, items):
        """Post the create page, reading the formset prefix from it."""
        self.client.force_login(self.user)
        prefix = self.client.get(INVOICE_CREATE_URL).context[
            "formset"
        ].prefix
        return self.client.post(
            INVOICE_CREATE_URL,
            {**form_data, **item_formset_data(prefix, items)},
        )

    def test_create_redirects_anonymous_users_to_login(self):
        response = self.client.get(INVOICE_CREATE_URL)
        self.assertRedirects(
            response, f"{LOGIN_URL}?next={INVOICE_CREATE_URL}"
        )

    def test_create_saves_an_invoice_with_line_items_and_the_total_is_right(self):
        response = self._post_invoice(
            invoice_form_data(self.client_obj, self.project),
            [
                {"description": "Design work", "quantity": "2",
                 "unit_price": "10.00"},
                {"description": "Hosting", "quantity": "3",
                 "unit_price": "5.50"},
            ],
        )
        invoice = Invoice.objects.get(number="INV-0001")
        self.assertEqual(invoice.owner, self.user)
        self.assertEqual(invoice.client, self.client_obj)
        self.assertEqual(invoice.project, self.project)
        self.assertEqual(invoice.status, Invoice.Status.DRAFT)
        self.assertEqual(invoice.items.count(), 2)
        self.assertEqual(invoice.total, Decimal("36.50"))
        self.assertRedirects(
            response, reverse("billing:detail", args=[invoice.pk])
        )

    def test_create_without_a_client_saves_nothing(self):
        self.client.force_login(self.user)
        prefix = self.client.get(INVOICE_CREATE_URL).context[
            "formset"
        ].prefix
        form_data = invoice_form_data(self.client_obj)
        form_data["client"] = ""
        response = self.client.post(
            INVOICE_CREATE_URL,
            {
                **form_data,
                **item_formset_data(
                    prefix,
                    [{"description": "Design work", "quantity": "1",
                      "unit_price": "10.00"}],
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_create_without_any_line_items_saves_nothing(self):
        response = self._post_invoice(
            invoice_form_data(self.client_obj, self.project),
            [{"description": "", "quantity": "", "unit_price": ""}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_client_dropdown_only_lists_the_signed_in_users_clients(self):
        make_client(self.other, name="Omar Farooq")
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_CREATE_URL)
        form = response.context["form"]
        client_ids = [c.pk for c in form.fields["client"].queryset]
        self.assertEqual(client_ids, [self.client_obj.pk])

    def test_project_dropdown_only_lists_the_signed_in_users_projects(self):
        other_client = make_client(self.other, name="Omar Farooq")
        make_project(self.other, other_client, name="Beta shop")
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_CREATE_URL)
        form = response.context["form"]
        project_ids = [p.pk for p in form.fields["project"].queryset]
        self.assertEqual(project_ids, [self.project.pk])

    def test_create_with_another_users_client_is_rejected(self):
        other_client = make_client(self.other, name="Omar Farooq")
        response = self._post_invoice(
            invoice_form_data(other_client, self.project),
            [{"description": "Design work", "quantity": "1",
              "unit_price": "10.00"}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_create_with_another_users_project_is_rejected(self):
        other_client = make_client(self.other, name="Omar Farooq")
        other_project = make_project(
            self.other, other_client, name="Beta shop"
        )
        response = self._post_invoice(
            invoice_form_data(self.client_obj, other_project),
            [{"description": "Design work", "quantity": "1",
              "unit_price": "10.00"}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invoice.objects.count(), 0)


class InvoiceDetailTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.invoice = make_invoice(self.user, self.client_obj)
        make_item(
            self.invoice, "Design work", quantity="2", unit_price="10.00"
        )
        make_item(
            self.invoice, "Hosting", quantity="3", unit_price="5.50"
        )

    def test_detail_shows_the_items_and_the_total(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("billing:detail", args=[self.invoice.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invoice.number)
        self.assertContains(response, self.client_obj.name)
        self.assertContains(response, "Design work")
        self.assertContains(response, "Hosting")
        self.assertContains(response, "20.00")
        self.assertContains(response, "16.50")
        self.assertContains(response, "36.50")

    def test_detail_of_another_users_invoice_answers_404(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        other_invoice = make_invoice(self.other, other_client)
        response = self.client.get(
            reverse("billing:detail", args=[other_invoice.pk])
        )
        self.assertEqual(response.status_code, 404)


class InvoiceModelTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_str_returns_the_number(self):
        invoice = make_invoice(self.user, self.client_obj)
        self.assertEqual(str(invoice), "INV-0001")

    def test_numbers_run_in_sequence_per_owner(self):
        first = make_invoice(self.user, self.client_obj)
        second = make_invoice(self.user, self.client_obj)
        other_client = make_client(self.other, name="Omar Farooq")
        other_first = make_invoice(self.other, other_client)
        self.assertEqual(first.number, "INV-0001")
        self.assertEqual(second.number, "INV-0002")
        self.assertEqual(other_first.number, "INV-0001")

    def test_line_total_multiplies_quantity_by_unit_price(self):
        invoice = make_invoice(self.user, self.client_obj)
        item = make_item(
            invoice, "Design work", quantity="2.5", unit_price="19.99"
        )
        self.assertEqual(item.line_total, Decimal("49.975"))

    def test_line_total_with_whole_numbers(self):
        invoice = make_invoice(self.user, self.client_obj)
        item = make_item(
            invoice, "Design work", quantity="3", unit_price="25.00"
        )
        self.assertEqual(item.line_total, Decimal("75.00"))

    def test_invoice_with_no_line_items_totals_zero(self):
        invoice = make_invoice(self.user, self.client_obj)
        self.assertEqual(invoice.total, Decimal("0"))
        self.assertEqual(invoice.items.count(), 0)

    def test_invoice_total_sums_all_line_items(self):
        invoice = make_invoice(self.user, self.client_obj)
        make_item(invoice, "Design work", quantity="2", unit_price="10.00")
        make_item(invoice, "Hosting", quantity="3", unit_price="5.50")
        self.assertEqual(invoice.total, Decimal("36.50"))

    def test_is_overdue_when_unpaid_and_past_due(self):
        invoice = make_invoice(
            self.user, self.client_obj, due_date=PAST
        )
        self.assertTrue(invoice.is_overdue)

    def test_is_not_overdue_when_paid_even_if_past_due(self):
        invoice = make_invoice(
            self.user,
            self.client_obj,
            status=Invoice.Status.PAID,
            due_date=PAST,
        )
        self.assertFalse(invoice.is_overdue)

    def test_is_not_overdue_when_due_date_is_in_the_future(self):
        invoice = make_invoice(
            self.user, self.client_obj, due_date=FUTURE
        )
        self.assertFalse(invoice.is_overdue)

    def test_is_not_overdue_when_there_is_no_due_date(self):
        invoice = make_invoice(
            self.user, self.client_obj, due_date=None
        )
        self.assertFalse(invoice.is_overdue)

    def test_owner_and_client_can_reach_the_invoice(self):
        invoice = make_invoice(self.user, self.client_obj)
        self.assertIn(invoice, list(self.user.invoices.all()))
        self.assertIn(invoice, list(self.client_obj.invoices.all()))
