"""Task list, detail, create, update and delete views.

Every view needs a signed-in user. Every query is scoped to
owner=request.user, so a task that belongs to someone else simply
does not exist for this user — opening, editing or deleting it answers
with a 404, never a permission page and never the other user's data.
The task list and creation live under their project
(/projects/<pk>/tasks/); the project dropdown only offers the signed-in
user's own projects, so a task can never be attached to a project that
belongs to someone else.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from apps.projects.models import Project

from .forms import TaskForm
from .models import Task


def _get_task(request, pk):
    """Fetch one of the signed-in user's tasks, or 404."""
    return get_object_or_404(Task, pk=pk, owner=request.user)


def _get_project(request, project_pk):
    """Fetch one of the signed-in user's projects, or 404."""
    return get_object_or_404(Project, pk=project_pk, owner=request.user)


@login_required
def task_list(request, project_pk):
    """List the signed-in user's tasks for one project, soonest due
    date first. Tasks without a due date come last, then newest first.
    """
    project = _get_project(request, project_pk)
    tasks = (
        Task.objects.filter(project=project, owner=request.user)
        .select_related("project")
        .order_by(F("due_date").asc(nulls_last=True), "-created")
    )
    return render(
        request, "tasks/list.html", {"tasks": tasks, "project": project}
    )


@login_required
def task_detail(request, pk):
    task = _get_task(request, pk)
    return render(request, "tasks/detail.html", {"task": task})


@login_required
def task_create(request, project_pk):
    project = _get_project(request, project_pk)
    if request.method == "POST":
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            # The project in the URL is authoritative: a task created
            # here always belongs to this project.
            task.project = project
            task.save()
            messages.success(request, f"Task {task.title} added.")
            return redirect("tasks:detail", pk=task.pk)
    else:
        form = TaskForm(user=request.user, initial={"project": project})
    return render(
        request, "tasks/form.html", {"form": form, "project": project}
    )


@login_required
def task_update(request, pk):
    task = _get_task(request, pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Task {task.title} updated.")
            return redirect("tasks:detail", pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    return render(request, "tasks/form.html", {"form": form, "task": task})


@login_required
def task_delete(request, pk):
    task = _get_task(request, pk)
    if request.method == "POST":
        title = task.title
        project_pk = task.project_id
        task.delete()
        messages.success(request, f"Task {title} deleted.")
        return redirect("projects:task-list", project_pk=project_pk)
    return render(request, "tasks/confirm_delete.html", {"task": task})
