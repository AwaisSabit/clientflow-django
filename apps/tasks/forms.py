"""Form for creating and editing a task.

The project dropdown only ever offers the signed-in user's own
projects — a task can never be attached to someone else's project.
"""
from django import forms

from apps.projects.models import Project

from .models import Task


class TaskForm(forms.ModelForm):
    """Create or update a task: title, description, project, status,
    priority, assignee and due date."""

    # Priority is optional in the form: a browser always sends the
    # selected option, but a post without one (or an empty value)
    # falls back to the model's default instead of failing.
    priority = forms.ChoiceField(
        choices=Task.Priority.choices,
        required=False,
        initial=Task.Priority.MEDIUM,
    )

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "project",
            "status",
            "priority",
            "assignee",
            "due_date",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_priority(self):
        """An empty priority means the default (medium)."""
        return self.cleaned_data.get("priority") or Task.Priority.MEDIUM

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["project"].queryset = Project.objects.filter(
                owner=user
            ).order_by("name")
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
