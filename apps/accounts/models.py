"""Custom user model for ClientFlow.

Defined on Day 1, before the first migration, so it can be changed later
only via a migration — never swap AUTH_USER_MODEL after data exists.
Day 2 adds registration / login / logout on top of this model.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A freelancer / team member. Extra profile fields arrive on Day 4."""

    display_name = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.display_name or self.username
