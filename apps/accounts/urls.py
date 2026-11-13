"""URLs for the accounts app: register, login and logout."""
from django.contrib.auth.views import LoginView
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
        ),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
]
