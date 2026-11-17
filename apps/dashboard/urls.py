"""URLs for the dashboard app: one page at /dashboard/."""
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
