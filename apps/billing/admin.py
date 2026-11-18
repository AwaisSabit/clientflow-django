"""Admin for the billing app."""
from django.contrib import admin

from .models import Invoice, InvoiceLineItem


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "client",
        "status",
        "issue_date",
        "due_date",
        "owner",
        "created",
    )
    list_filter = ("status", "owner")
    search_fields = ("number", "client__name")
    readonly_fields = ("number", "created", "updated")
    inlines = [InvoiceLineItemInline]


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ("description", "invoice", "quantity", "unit_price")
    search_fields = ("description", "invoice__number")
