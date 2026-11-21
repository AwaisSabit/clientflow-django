"""Invoice list, detail, create, edit and delete views.

Every view needs a signed-in user. Every query is scoped to
owner=request.user, so an invoice that belongs to someone else simply
does not exist for this user — opening, editing or deleting it answers
with a 404, never a permission page and never the other user's data.
The client and project dropdowns only offer the signed-in user's own
clients and projects, so an invoice can never be attached to another
user's client or project.
"""
import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    InvoiceForm,
    InvoiceLineItemEditFormSet,
    InvoiceLineItemFormSet,
)
from .models import Invoice

INVOICES_PER_PAGE = 10


def _get_invoice(request, pk):
    """Fetch one of the signed-in user's invoices, or 404.

    The client, project and line items come along in the same
    queries, so the detail page never asks the database once per
    line item.
    """
    return get_object_or_404(
        Invoice.objects.select_related("client", "project")
        .prefetch_related("items"),
        pk=pk,
        owner=request.user,
    )


@login_required
def invoice_list(request):
    """List the signed-in user's invoices, newest first, 10 per page.

    `status` narrows the list to one status (draft, sent, paid or
    overdue). Any other value is ignored and the full list is shown.
    The filter only ever sees the signed-in user's own invoices, and
    the page links keep it.
    """
    status_filter = request.GET.get("status", "").strip()
    if status_filter not in Invoice.Status.values:
        status_filter = ""
    invoices = (
        Invoice.objects.filter(owner=request.user)
        .select_related("client", "project")
        .order_by("-created")
    )
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    paginator = Paginator(invoices, INVOICES_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # The page links need the current status filter, but not the
    # page number itself.
    kept_params = request.GET.copy()
    kept_params.pop("page", None)
    query_string = kept_params.urlencode()

    return render(
        request,
        "invoices/list.html",
        {
            "invoices": page_obj,
            "page_obj": page_obj,
            "total_count": paginator.count,
            "status_filter": status_filter,
            "query_string": query_string,
        },
    )


@login_required
def invoice_export_csv(request):
    """Download the signed-in user's own invoices as a CSV file.

    One row per invoice: number, client, project (blank when there
    is none), status, issue date, due date and total. The same
    `status` filter as the list page applies, so exporting a
    filtered list only exports the invoices in that list. Another
    user's invoices never appear.
    """
    status_filter = request.GET.get("status", "").strip()
    if status_filter not in Invoice.Status.values:
        status_filter = ""
    invoices = (
        Invoice.objects.filter(owner=request.user)
        .select_related("client", "project")
        .prefetch_related("items")
        .order_by("-created")
    )
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="invoices.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(
        [
            "Number",
            "Client",
            "Project",
            "Status",
            "Issue date",
            "Due date",
            "Total",
        ]
    )
    for invoice in invoices:
        writer.writerow(
            [
                invoice.number,
                invoice.client.name,
                invoice.project.name if invoice.project else "",
                invoice.get_status_display(),
                invoice.issue_date.isoformat(),
                (
                    invoice.due_date.isoformat()
                    if invoice.due_date
                    else ""
                ),
                invoice.total.quantize(Decimal("0.01")),
            ]
        )
    return response


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


@login_required
def invoice_update(request, pk):
    """Edit an invoice and its line items.

    The invoice fields (client, project, status, dates) and the line
    items are edited on one page. Line items can be added or removed,
    but at least one must remain — deleting every item is rejected.
    """
    invoice = _get_invoice(request, pk)
    if request.method == "POST":
        form = InvoiceForm(
            request.POST, instance=invoice, user=request.user
        )
        formset = InvoiceLineItemEditFormSet(
            request.POST, instance=invoice
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(
                request, f"Invoice {invoice.number} updated."
            )
            return redirect("billing:detail", pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice, user=request.user)
        formset = InvoiceLineItemEditFormSet(instance=invoice)
    return render(
        request,
        "invoices/form.html",
        {"form": form, "formset": formset, "invoice": invoice},
    )


@login_required
def invoice_delete(request, pk):
    invoice = _get_invoice(request, pk)
    if request.method == "POST":
        number = invoice.number
        invoice.delete()
        messages.success(request, f"Invoice {number} deleted.")
        return redirect("billing:list")
    return render(
        request, "invoices/confirm_delete.html", {"invoice": invoice}
    )


@login_required
def invoice_status_change(request, pk):
    """Move an invoice one step forward, with a single button press.

    Only a POST changes anything. The new status comes from the
    posted "status" field and must be a move the invoice is allowed
    to make (see Invoice.ALLOWED_STATUS_CHANGES — draft can go to
    sent or paid, sent and overdue can go to paid, and paid is
    final). An invalid move changes nothing and shows an error.
    """
    invoice = _get_invoice(request, pk)
    if request.method != "POST":
        return redirect("billing:detail", pk=invoice.pk)
    new_status = request.POST.get("status", "")
    if new_status not in Invoice.Status.values:
        messages.error(request, "That is not a valid invoice status.")
    elif not invoice.can_move_to(new_status):
        messages.error(
            request,
            f"Invoice {invoice.number} cannot move from "
            f"{invoice.get_status_display()} to "
            f"{Invoice.Status(new_status).label}.",
        )
    else:
        invoice.status = new_status
        invoice.save()
        messages.success(
            request,
            f"Invoice {invoice.number} marked as "
            f"{invoice.get_status_display()}.",
        )
    return redirect("billing:detail", pk=invoice.pk)
