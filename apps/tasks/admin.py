"""Admin for the tasks app."""
from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "status", "due_date", "owner", "created")
    list_filter = ("status", "owner")
    search_fields = ("title", "description")
    readonly_fields = ("created", "updated")
