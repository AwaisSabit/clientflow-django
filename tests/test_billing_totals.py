"""Tests for invoice billing totals: decimals, zero lines, large
amounts and per-owner numbering. The totals are worked out from the
line items, so these tests pin the maths the invoice page and the
CSV export both rely on.
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

INVOICE_EXPORT_URL = reverse("billing:export")

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


class BillingTotalTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.client_obj = make_client(self.user)
        self.invoice = make_invoice(self.user, self.client_obj)

    def test_total_with_fractional_quantity_and_price_is_exact(self):
        make_item(
            self.invoice, "Small job", quantity="0.10",
            unit_price="0.30",
        )
        self.assertEqual(self.invoice.total, Decimal("0.03"))

    def test_total_with_two_decimal_quantity(self):
        make_item(
            self.invoice, "Design work", quantity="1.25",
            unit_price="4.00",
        )
        self.assertEqual(self.invoice.total, Decimal("5.00"))

    def test_total_is_a_decimal_not_a_float(self):
        make_item(self.invoice, "Design work", quantity="3",
                  unit_price="10.00")
        self.assertIsInstance(self.invoice.total, Decimal)

    def test_zero_quantity_line_adds_nothing(self):
        make_item(
            self.invoice, "Not started", quantity="0",
            unit_price="50.00",
        )
        make_item(
            self.invoice, "Design work", quantity="2",
            unit_price="10.00",
        )
        self.assertEqual(self.invoice.total, Decimal("20.00"))

    def test_zero_price_line_adds_nothing(self):
        make_item(
            self.invoice, "Free fix", quantity="5",
            unit_price="0.00",
        )
        make_item(
            self.invoice, "Design work", quantity="1",
            unit_price="25.00",
        )
        self.assertEqual(self.invoice.total, Decimal("25.00"))

    def test_total_sums_many_line_items(self):
        for number in range(5):
            make_item(
                self.invoice, f"Work {number}", quantity="2",
                unit_price="7.50",
            )
        self.assertEqual(self.invoice.total, Decimal("75.00"))

    def test_total_with_a_large_amount(self):
        make_item(
            self.invoice, "Big build", quantity="1000",
            unit_price="999.99",
        )
        self.assertEqual(self.invoice.total, Decimal("999990.00"))

    def test_line_total_with_fractional_quantity_and_price(self):
        item = make_item(
            self.invoice, "Design work", quantity="0.50",
            unit_price="19.99",
        )
        self.assertEqual(item.line_total, Decimal("9.995"))


class InvoiceNumberingTests(TestCase):
    def setUp(self):
        self.user = make_user("awais")
        self.other = make_user("bilal")
        self.client_obj = make_client(self.user)

    def test_numbers_keep_four_digits_up_to_twelve_invoices(self):
        invoices = [
            make_invoice(self.user, self.client_obj)
            for _ in range(12)
        ]
        self.assertEqual(invoices[0].number, "INV-0001")
        self.assertEqual(invoices[9].number, "INV-0010")
        self.assertEqual(invoices[11].number, "INV-0012")

    def test_numbering_continues_from_the_highest_remaining_invoice(self):
        first = make_invoice(self.user, self.client_obj)
        second = make_invoice(self.user, self.client_obj)
        third = make_invoice(self.user, self.client_obj)
        # Deleting the middle invoice leaves INV-0003 as the highest,
        # so the next invoice is INV-0004.
        second.delete()
        fourth = make_invoice(self.user, self.client_obj)
        self.assertEqual(
            [first.number, third.number, fourth.number],
            ["INV-0001", "INV-0003", "INV-0004"],
        )

    def test_deleting_the_newest_invoice_reuses_its_number(self):
        make_invoice(self.user, self.client_obj)
        newest = make_invoice(self.user, self.client_obj)
        newest.delete()
        replacement = make_invoice(self.user, self.client_obj)
        self.assertEqual(replacement.number, "INV-0002")

    def test_numbering_is_per_owner_even_with_many_invoices(self):
        other_client = make_client(self.other, name="Omar Farooq")
        for _ in range(12):
            make_invoice(self.user, self.client_obj)
        other_first = make_invoice(self.other, other_client)
        self.assertEqual(other_first.number, "INV-0001")

    def test_export_covers_every_invoice_not_just_the_first_page(self):
        for _ in range(12):
            invoice = make_invoice(self.user, self.client_obj)
            make_item(invoice)
        self.client.force_login(self.user)
        response = self.client.get(INVOICE_EXPORT_URL)
        rows = response.content.decode().strip().splitlines()
        # One header row plus one row per invoice.
        self.assertEqual(len(rows), 13)
        self.assertTrue(rows[0].startswith("Number,Client,Project"))
        self.assertIn("INV-0012", response.content.decode())
