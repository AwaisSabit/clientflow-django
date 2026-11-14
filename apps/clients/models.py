"""Client model for ClientFlow.

Each client belongs to one user (the owner). A user can only see, edit
or delete their own clients — the views enforce that, so one user's
clients never leak into another user's list.
"""
from django.conf import settings
from django.db import models


class Client(models.Model):
    """A person or business the freelancer works for."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
