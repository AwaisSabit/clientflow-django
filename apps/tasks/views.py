"""Task list, detail, create, update and delete views.

Every view needs a signed-in user. Every query is scoped to
owner=request.user, so a task that belongs to someone else simply
does not exist for this user — opening, editing or deleting it answers
with a 404, never a permission page and never the other user's data.
The client dropdown only offers the signed-in user's own clients, so
a task can never be attached to a client that belongs to someone else.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Task


def _get_task(request, pk):
    """Fetch one of the signed-in user's tasks, or 404."""
    return get_object_or_404(Task, pk=pk, owner=request.user)


@login_required
def task_list(request):
    """List the signed-in user's tasks, soonest due date first.

    Tasks without a due date come last, then newest first.
    """
    tasks = (
        Task.objects.filter(owner=request.user)
        .select_related("client")
        .order_by(F("due_date").asc(nulls_last=True), "-created")
    )
    return render(request, "tasks/list.html", {"tasks": tasks})


@login_required
def task_detail(request, pk):
    task = _get_task(request, pk)
    return render(request, "tasks/detail.html", {"task": task})


@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            messages.success(request, f"Task {task.title} added.")
            return redirect("tasks:detail", pk=task.pk)
    else:
        form = TaskForm(user=request.user)
    return render(request, "tasks/form.html", {"form": form})


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
        task.delete()
        messages.success(request, f"Task {title} deleted.")
        return redirect("tasks:list")
    return render(request, "tasks/confirm_delete.html", {"task": task})
