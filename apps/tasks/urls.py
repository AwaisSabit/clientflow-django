"""URLs for the tasks app: detail, edit, delete.

The task list and creation live under their project
(/projects/<pk>/tasks/), so those routes are in the projects app.
"""
from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("<int:pk>/", views.task_detail, name="detail"),
    path("<int:pk>/edit/", views.task_update, name="update"),
    path("<int:pk>/delete/", views.task_delete, name="delete"),
]
