"""Admin for the projects app."""
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "status", "due_date", "owner", "created")
    list_filter = ("status", "owner")
    search_fields = ("name", "description")
    readonly_fields = ("created", "updated")
