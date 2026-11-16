"""Form for creating and editing a project."""
from django import forms

from apps.clients.models import Client

from .models import Project


class ProjectForm(forms.ModelForm):
    """Create or update a project: name, client, description, status
    and dates."""

    class Meta:
        model = Project
        fields = (
            "name",
            "client",
            "description",
            "status",
            "start_date",
            "due_date",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
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
