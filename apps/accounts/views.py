"""Registration, login and logout for ClientFlow.

Login uses Django's built-in LoginView. Registration saves a new user
with the custom User model, signs them in straight away and sends them
to the home page. Logout is a small function view so the navigation
link can sign the user out and return them home.
"""
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("home")
