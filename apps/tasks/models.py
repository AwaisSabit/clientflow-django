"""Task model for ClientFlow.

Each task belongs to one user (the owner) and is linked to one of that
user's clients. A user can only see, edit or delete their own tasks —
the views enforce that, so one user's tasks never leak into another
user's list.
"""
from django.conf import settings
from django.db import models


class Task(models.Model):
    """A piece of work to do for a client."""

    class Status(models.TextChoices):
        TODO = "to_do", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    due_date = models.DateField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title
