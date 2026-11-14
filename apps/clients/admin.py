"""Admin for the clients app."""
from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "email", "owner", "created")
    list_filter = ("owner",)
    search_fields = ("name", "company", "email")
    readonly_fields = ("created", "updated")
