"""Admin for the tasks app."""
from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "status",
        "priority",
        "assignee",
        "due_date",
        "owner",
        "created",
    )
    list_filter = ("status", "priority", "owner", "project")
    search_fields = ("title", "description")
    readonly_fields = ("created", "updated")
