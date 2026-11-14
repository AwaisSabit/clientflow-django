"""Form for creating and editing a client."""
from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    """Create or update a client: name, email, phone, company, notes."""

    class Meta:
        model = Client
        fields = ("name", "email", "phone", "company", "notes")
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
