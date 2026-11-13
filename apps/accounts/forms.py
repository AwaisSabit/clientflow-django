"""Forms for the accounts app: registration on top of the custom User."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Sign-in form, with Bootstrap styling on its fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class RegistrationForm(UserCreationForm):
    """Create a new account: username, email, display name, password twice."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "display_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
