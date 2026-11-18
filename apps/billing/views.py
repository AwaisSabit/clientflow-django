"""Invoice list, detail and create views.

Every view needs a signed-in user. Every query is scoped to
owner=request.user, so an invoice that belongs to someone else simply
does not exist for this user — opening it answers with a 404, never a
permission page and never the other user's data. The client and
project dropdowns only offer the signed-in user's own clients and
projects, so an invoice can never be attached to another user's
client or project.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InvoiceForm, InvoiceLineItemFormSet
from .models import Invoice


def _get_invoice(request, pk):
    """Fetch one of the signed-in user's invoices, or 404."""
    return get_object_or_404(Invoice, pk=pk, owner=request.user)


@login_required
def invoice_list(request):
    """List the signed-in user's invoices, newest first."""
    invoices = (
        Invoice.objects.filter(owner=request.user)
        .select_related("client", "project")
        .order_by("-created")
    )
    return render(request, "invoices/list.html", {"invoices": invoices})


@login_required
def invoice_detail(request, pk):
    invoice = _get_invoice(request, pk)
    return render(
        request, "invoices/detail.html", {"invoice": invoice}
    )


@login_required
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST, user=request.user)
        formset = InvoiceLineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.owner = request.user
            invoice.save()
            formset.instance = invoice
            formset.save()
            messages.success(
                request, f"Invoice {invoice.number} added."
            )
            return redirect("billing:detail", pk=invoice.pk)
    else:
        form = InvoiceForm(user=request.user)
        formset = InvoiceLineItemFormSet()
    return render(
        request,
        "invoices/form.html",
        {"form": form, "formset": formset},
    )
