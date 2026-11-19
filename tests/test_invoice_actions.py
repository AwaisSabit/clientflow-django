"""Tests for invoice editing, deletion, status changes and CSV
export. Every test is written from the owner's point of view: a
signed-in user can only edit, delete, move or export their own
invoices, and an invoice that belongs to someone else answers with
a 404.
"""
import csv
import io
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
INVOICE_EXPORT_URL = reverse("billing:export")
LOGIN_URL = reverse("accounts:login")

GOOD_PASSWORD = "testpass123"
TODAY = date.today()
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
    """Management form plus one row per item dict. Rows may carry an
    "id" (for an existing line item) and "DELETE" ("on" to remove it).
    """
    data = {
        f"{prefix}-TOTAL_FORMS": str(len(items)),
        f"{prefix}-INITIAL_FORMS": str(
            sum(1 for item in items if "id" in item)
        ),
        f"{prefix}-MIN_NUM_FORMS": "1",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }
    for i, item in enumerate(items):
        if "id" in item:
            data[f"{prefix}-{i}-id"] = str(item["id"])
        data[f"{prefix}-{i}-description"] = item.get(
            "description", ""
        )
        data[f"{prefix}-{i}-quantity"] = item.get("quantity", "")
        data[f"{prefix}-{i}-unit_price"] = item.get("unit_price", "")
        if item.get("DELETE"):
            data[f"{prefix}-{i}-DELETE"] = "on"
    return data


class InvoiceUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)
        self.invoice = make_invoice(
            self.user, self.client_obj, self.project
        )
        self.item = make_item(
            self.invoice, "Design work", quantity="2",
            unit_price="10.00",
        )

    def _edit_url(self, invoice=None):
        invoice = invoice or self.invoice
        return reverse("billing:update", args=[invoice.pk])

    def _post_edit(self, form_data, items):
        """Post the edit page, reading the formset prefix from it."""
        self.client.force_login(self.user)
        prefix = self.client.get(self._edit_url()).context[
            "formset"
        ].prefix
        return self.client.post(
            self._edit_url(),
            {**form_data, **item_formset_data(prefix, items)},
        )

    def _existing_item_row(self, **overrides):
        row = {
            "id": self.item.pk,
            "description": "Design work",
            "quantity": "2",
            "unit_price": "10.00",
        }
        row.update(overrides)
        return row

    def test_edit_redirects_anonymous_users_to_login(self):
        url = self._edit_url()
        response = self.client.get(url)
        self.assertRedirects(response, f"{LOGIN_URL}?next={url}")

    def test_edit_page_shows_the_invoice_and_its_items(self):
        self.client.force_login(self.user)
        response = self.client.get(self._edit_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invoice.number)
        self.assertContains(response, "Design work")
        self.assertContains(response, "Save changes")

    def test_edit_saves_changes_and_redirects_to_the_detail_page(self):
        response = self._post_edit(
            invoice_form_data(
                self.client_obj,
                self.project,
                status=Invoice.Status.SENT,
            ),
            [self._existing_item_row(quantity="3")],
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.SENT)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("3"))
        self.assertEqual(self.invoice.total, Decimal("30.00"))
        self.assertRedirects(
            response,
            reverse("billing:detail", args=[self.invoice.pk]),
        )

    def test_edit_can_add_a_line_item(self):
        response = self._post_edit(
            invoice_form_data(self.client_obj, self.project),
            [
                self._existing_item_row(),
                {
                    "description": "Hosting",
                    "quantity": "1",
                    "unit_price": "5.50",
                },
            ],
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.invoice.items.count(), 2)
        self.assertEqual(self.invoice.total, Decimal("25.50"))

    def test_edit_can_remove_a_line_item(self):
        second = make_item(
            self.invoice, "Hosting", quantity="1",
            unit_price="5.50",
        )
        response = self._post_edit(
            invoice_form_data(self.client_obj, self.project),
            [
                self._existing_item_row(),
                {
                    "id": second.pk,
                    "description": "Hosting",
                    "quantity": "1",
                    "unit_price": "5.50",
                    "DELETE": True,
                },
            ],
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.invoice.items.count(), 1)
        self.assertFalse(
            InvoiceLineItem.objects.filter(pk=second.pk).exists()
        )
        self.assertEqual(self.invoice.total, Decimal("20.00"))

    def test_edit_that_removes_every_line_item_saves_nothing(self):
        response = self._post_edit(
            invoice_form_data(self.client_obj, self.project),
            [self._existing_item_row(DELETE=True)],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.invoice.items.count(), 1)
        self.assertEqual(self.invoice.total, Decimal("20.00"))

    def test_edit_of_another_users_invoice_answers_404(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        other_invoice = make_invoice(self.other, other_client)
        url = self._edit_url(other_invoice)
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(
            url,
            invoice_form_data(self.client_obj, self.project),
        )
        self.assertEqual(response.status_code, 404)
        other_invoice.refresh_from_db()
        self.assertEqual(other_invoice.status, Invoice.Status.DRAFT)

    def test_edit_with_another_users_client_is_rejected(self):
        other_client = make_client(self.other, name="Omar Farooq")
        response = self._post_edit(
            invoice_form_data(other_client, self.project),
            [self._existing_item_row()],
        )
        self.assertEqual(response.status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.client, self.client_obj)


class InvoiceDeleteTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.invoice = make_invoice(self.user, self.client_obj)
        make_item(self.invoice)

    def _delete_url(self, invoice=None):
        invoice = invoice or self.invoice
        return reverse("billing:delete", args=[invoice.pk])

    def test_delete_redirects_anonymous_users_to_login(self):
        url = self._delete_url()
        response = self.client.get(url)
        self.assertRedirects(response, f"{LOGIN_URL}?next={url}")

    def test_delete_asks_for_confirmation(self):
        self.client.force_login(self.user)
        response = self.client.get(self._delete_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invoice.number)
        self.assertContains(response, "Yes, delete this invoice")

    def test_delete_removes_the_invoice_and_its_items(self):
        self.client.force_login(self.user)
        response = self.client.post(self._delete_url())
        self.assertRedirects(response, INVOICE_LIST_URL)
        self.assertFalse(
            Invoice.objects.filter(pk=self.invoice.pk).exists()
        )
        self.assertEqual(InvoiceLineItem.objects.count(), 0)

    def test_delete_of_another_users_invoice_answers_404(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        other_invoice = make_invoice(self.other, other_client)
        url = self._delete_url(other_invoice)
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Invoice.objects.filter(pk=other_invoice.pk).exists()
        )


class InvoiceStatusChangeTests(TestCase):
    """One-click status moves: draft -> sent, draft -> paid,
    sent -> paid and overdue -> paid are allowed; paid is final,
    and anything else changes nothing and shows an error."""

    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.invoice = make_invoice(self.user, self.client_obj)

    def _status_url(self, invoice=None):
        invoice = invoice or self.invoice
        return reverse("billing:status", args=[invoice.pk])

    def _post_status(self, status, invoice=None):
        self.client.force_login(self.user)
        return self.client.post(
            self._status_url(invoice), {"status": status}
        )

    def test_draft_invoice_can_be_marked_as_sent(self):
        response = self._post_status(Invoice.Status.SENT)
        self.assertRedirects(
            response,
            reverse("billing:detail", args=[self.invoice.pk]),
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.SENT)

    def test_draft_invoice_can_be_marked_as_paid(self):
        self._post_status(Invoice.Status.PAID)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)

    def test_sent_invoice_can_be_marked_as_paid(self):
        self.invoice.status = Invoice.Status.SENT
        self.invoice.save()
        self._post_status(Invoice.Status.PAID)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)

    def test_overdue_invoice_can_be_marked_as_paid(self):
        self.invoice.status = Invoice.Status.OVERDUE
        self.invoice.save()
        self._post_status(Invoice.Status.PAID)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)

    def test_paid_invoice_is_final_and_cannot_go_back_to_sent(self):
        self.invoice.status = Invoice.Status.PAID
        self.invoice.save()
        response = self._post_status(Invoice.Status.SENT)
        self.assertRedirects(
            response,
            reverse("billing:detail", args=[self.invoice.pk]),
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any("cannot move" in str(m) for m in messages)
        )

    def test_sent_invoice_cannot_go_back_to_draft(self):
        self.invoice.status = Invoice.Status.SENT
        self.invoice.save()
        self._post_status(Invoice.Status.DRAFT)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.SENT)

    def test_paid_invoice_cannot_be_marked_overdue(self):
        self.invoice.status = Invoice.Status.PAID
        self.invoice.save()
        self._post_status(Invoice.Status.OVERDUE)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)

    def test_an_unknown_status_value_changes_nothing(self):
        response = self._post_status("archived")
        self.assertRedirects(
            response,
            reverse("billing:detail", args=[self.invoice.pk]),
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.DRAFT)

    def test_a_get_request_changes_nothing(self):
        self.client.force_login(self.user)
        response = self.client.get(
            self._status_url(), {"status": Invoice.Status.PAID}
        )
        self.assertRedirects(
            response,
            reverse("billing:detail", args=[self.invoice.pk]),
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.DRAFT)

    def test_status_change_of_another_users_invoice_answers_404(self):
        self.client.force_login(self.user)
        other_client = make_client(self.other, name="Omar Farooq")
        other_invoice = make_invoice(self.other, other_client)
        response = self.client.post(
            self._status_url(other_invoice),
            {"status": Invoice.Status.PAID},
        )
        self.assertEqual(response.status_code, 404)
        other_invoice.refresh_from_db()
        self.assertEqual(other_invoice.status, Invoice.Status.DRAFT)

    def test_status_change_redirects_anonymous_users_to_login(self):
        url = self._status_url()
        response = self.client.post(
            url, {"status": Invoice.Status.SENT}
        )
        self.assertRedirects(response, f"{LOGIN_URL}?next={url}")

    def test_detail_page_offers_the_right_buttons_for_each_status(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("billing:detail", args=[self.invoice.pk])
        )
        self.assertContains(response, "Mark as sent")
        self.assertContains(response, "Mark as paid")

        self.invoice.status = Invoice.Status.SENT
        self.invoice.save()
        response = self.client.get(
            reverse("billing:detail", args=[self.invoice.pk])
        )
        self.assertNotContains(response, "Mark as sent")
        self.assertContains(response, "Mark as paid")

        self.invoice.status = Invoice.Status.PAID
        self.invoice.save()
        response = self.client.get(
            reverse("billing:detail", args=[self.invoice.pk])
        )
        self.assertNotContains(response, "Mark as sent")
        self.assertNotContains(response, "Mark as paid")


class InvoiceListStatusFilterTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.draft = make_invoice(
            self.user, self.client_obj, status=Invoice.Status.DRAFT
        )
        self.paid = make_invoice(
            self.user, self.client_obj, status=Invoice.Status.PAID
        )
        other_client = make_client(self.other, name="Omar Farooq")
        self.other_paid = make_invoice(
            self.other, other_client, status=Invoice.Status.PAID
        )

    def test_filter_narrows_the_list_to_one_status(self):
        self.client.force_login(self.user)
        response = self.client.get(
            INVOICE_LIST_URL, {"status": Invoice.Status.PAID}
        )
        invoices = list(response.context["invoices"])
        self.assertEqual(invoices, [self.paid])
        self.assertContains(response, self.paid.number)
        self.assertNotContains(response, self.draft.number)

    def test_filter_never_shows_another_users_invoices(self):
        self.client.force_login(self.user)
        response = self.client.get(
            INVOICE_LIST_URL, {"status": Invoice.Status.PAID}
        )
        invoices = list(response.context["invoices"])
        self.assertNotIn(self.other_paid, invoices)

    def test_an_unknown_status_value_shows_the_full_list(self):
        self.client.force_login(self.user)
        response = self.client.get(
            INVOICE_LIST_URL, {"status": "archived"}
        )
        invoices = list(response.context["invoices"])
        self.assertEqual(invoices, [self.paid, self.draft])

    def test_filter_with_no_match_shows_the_filtered_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(
            INVOICE_LIST_URL, {"status": Invoice.Status.OVERDUE}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No invoices with this status")


class InvoiceExportCsvTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)
        self.project = make_project(self.user, self.client_obj)
        self.draft = make_invoice(
            self.user,
            self.client_obj,
            self.project,
            status=Invoice.Status.DRAFT,
        )
        make_item(
            self.draft, "Design work", quantity="2",
            unit_price="10.00",
        )
        self.paid = make_invoice(
            self.user,
            self.client_obj,
            status=Invoice.Status.PAID,
            due_date=None,
        )
        make_item(
            self.paid, "Hosting", quantity="3", unit_price="5.50"
        )
        other_client = make_client(self.other, name="Omar Farooq")
        self.other_invoice = make_invoice(self.other, other_client)
        make_item(self.other_invoice)

    def _read_csv(self, response):
        return list(
            csv.reader(io.StringIO(response.content.decode("utf-8")))
        )

    def test_export_downloads_a_csv_with_headers_and_one_row_per_invoice(self):
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_EXPORT_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="invoices.csv"',
        )
        rows = self._read_csv(response)
        self.assertEqual(
            rows[0],
            [
                "Number",
                "Client",
                "Project",
                "Status",
                "Issue date",
                "Due date",
                "Total",
            ],
        )
        # Newest first, so the paid invoice comes before the draft.
        self.assertEqual(rows[1][0], self.paid.number)
        self.assertEqual(rows[1][1], "Sara Khan")
        self.assertEqual(rows[1][2], "")
        self.assertEqual(rows[1][3], "Paid")
        self.assertEqual(rows[1][4], TODAY.isoformat())
        self.assertEqual(rows[1][5], "")
        self.assertEqual(rows[1][6], "16.50")
        self.assertEqual(rows[2][0], self.draft.number)
        self.assertEqual(rows[2][2], "Website redesign")
        self.assertEqual(rows[2][3], "Draft")
        self.assertEqual(rows[2][5], FUTURE.isoformat())
        self.assertEqual(rows[2][6], "20.00")

    def test_export_never_includes_another_users_invoices(self):
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_EXPORT_URL)
        rows = self._read_csv(response)
        # Numbers restart per owner, so the other user's invoice is
        # also INV-0001 — the client name is what tells them apart.
        self.assertEqual(len(rows), 3)
        self.assertNotIn(
            "Omar Farooq",
            response.content.decode("utf-8"),
        )

    def test_export_honours_the_status_filter(self):
        self.client.force_login(self.user)
        response = self.client.get(
            INVOICE_EXPORT_URL, {"status": Invoice.Status.PAID}
        )
        rows = self._read_csv(response)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], self.paid.number)

    def test_export_with_no_invoices_returns_only_the_header_row(self):
        empty_user = make_user("hassan")
        self.client.force_login(empty_user)
        response = self.client.get(INVOICE_EXPORT_URL)
        self.assertEqual(response.status_code, 200)
        rows = self._read_csv(response)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Number")

    def test_export_redirects_anonymous_users_to_login(self):
        response = self.client.get(INVOICE_EXPORT_URL)
        self.assertRedirects(
            response, f"{LOGIN_URL}?next={INVOICE_EXPORT_URL}"
        )
