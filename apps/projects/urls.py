"""URLs for the projects app: list, create, detail, edit, delete,
plus the task list and creation nested under one project.
"""
from django.urls import path

from apps.tasks import views as task_views

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="list"),
    path("add/", views.project_create, name="create"),
    path("<int:pk>/", views.project_detail, name="detail"),
    path("<int:pk>/edit/", views.project_update, name="update"),
    path("<int:pk>/delete/", views.project_delete, name="delete"),
    path(
        "<int:project_pk>/tasks/", task_views.task_list, name="task-list"
    ),
    path(
        "<int:project_pk>/tasks/add/",
        task_views.task_create,
        name="task-create",
    ),
]
