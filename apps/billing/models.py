"""Invoice and invoice line item models for ClientFlow.

Each invoice belongs to one user (the owner) and is billed to one of
that user's clients, optionally for one of their projects. The views
enforce ownership, so one user's invoices never leak into another
user's list. Invoice numbers are generated on first save, sequential
per owner (INV-0001, INV-0002, ...), and unique per owner.
"""
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models


class Invoice(models.Model):
    """A bill for a client, made up of line items."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    # One-click status changes on the invoice page may only move an
    # invoice forward: draft -> sent, draft -> paid, sent -> paid,
    # overdue -> paid. Paid is final — a paid invoice cannot be
    # reopened with a one-click button. Overdue is set from the edit
    # form, never by a one-click button. The edit form sets the
    # status directly and does not enforce these transitions.
    ALLOWED_STATUS_CHANGES = {
        Status.DRAFT: {Status.SENT, Status.PAID},
        Status.SENT: {Status.PAID},
        Status.OVERDUE: {Status.PAID},
        Status.PAID: set(),
    }

    def can_move_to(self, new_status):
        """True when a one-click status change to new_status is allowed."""
        return new_status in self.ALLOWED_STATUS_CHANGES.get(
            self.status, set()
        )

    number = models.CharField(
        max_length=20, blank=True, editable=False
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    issue_date = models.DateField(default=date.today)
    due_date = models.DateField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "number"], name="unique_number_per_owner"
            )
        ]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._next_number()
        super().save(*args, **kwargs)

    def _next_number(self):
        """Next invoice number for this owner, e.g. INV-0003."""
        last = (
            Invoice.objects.filter(owner=self.owner)
            .exclude(number="")
            .order_by("-number")
            .values_list("number", flat=True)
            .first()
        )
        next_value = 1
        if last:
            try:
                next_value = int(last.rsplit("-", 1)[-1]) + 1
            except ValueError:
                next_value = 1
        return f"INV-{next_value:04d}"

    @property
    def total(self):
        """Sum of the line item totals; zero when there are none."""
        return sum(
            (item.line_total for item in self.items.all()),
            Decimal("0"),
        )

    @property
    def is_overdue(self):
        """True when unpaid and the due date has passed."""
        return (
            self.status != self.Status.PAID
            and self.due_date is not None
            and self.due_date < date.today()
        )


class InvoiceLineItem(models.Model):
    """One billed line on an invoice: what, how many, at what price."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("1")
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.description

    @property
    def line_total(self):
        """Quantity times unit price."""
        return self.quantity * self.unit_price
