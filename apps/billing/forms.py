"""Forms for creating an invoice and its line items."""
from django import forms
from django.forms import inlineformset_factory

from apps.clients.models import Client
from apps.projects.models import Project

from .models import Invoice, InvoiceLineItem


class InvoiceForm(forms.ModelForm):
    """Create an invoice: client, optional project, status and dates."""

    class Meta:
        model = Invoice
        fields = (
            "client",
            "project",
            "status",
            "issue_date",
            "due_date",
        )
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["client"].queryset = Client.objects.filter(
                owner=user
            ).order_by("name")
            self.fields["project"].queryset = Project.objects.filter(
                owner=user
            ).order_by("name")
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class InvoiceLineItemForm(forms.ModelForm):
    """One line on the invoice: what, how many, at what price."""

    class Meta:
        model = InvoiceLineItem
        fields = ("description", "quantity", "unit_price")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


# Line items are added on the invoice page itself. At least one line
# item is required: an invoice with no lines cannot be saved.
InvoiceLineItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceLineItem,
    form=InvoiceLineItemForm,
    fields=("description", "quantity", "unit_price"),
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=False,
)
