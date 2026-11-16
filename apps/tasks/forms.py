"""Form for creating and editing a task.

The client dropdown only ever offers the signed-in user's own
clients — a task can never be attached to someone else's client.
"""
from django import forms

from apps.clients.models import Client

from .models import Task


class TaskForm(forms.ModelForm):
    """Create or update a task: title, description, client, status and
    due date."""

    class Meta:
        model = Task
        fields = ("title", "description", "client", "status", "due_date")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["client"].queryset = Client.objects.filter(
                owner=user
            ).order_by("name")
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
