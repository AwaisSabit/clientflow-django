"""Dashboard view for ClientFlow.

One page that sums up the signed-in user's own work: how many clients,
projects and tasks they have, how their tasks split by status, which
tasks are overdue, and their newest items. Everything is filtered on
owner=request.user, so another user's counts or items never appear here.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.tasks.models import Task


@login_required
def dashboard(request):
    """Show the signed-in user's own counts, overdue tasks and recent items."""
    user = request.user
    tasks = user.tasks.all()
    overdue_tasks = (
        tasks.filter(due_date__lt=timezone.localdate())
        .exclude(status=Task.Status.DONE)
        .order_by("due_date")
    )
    context = {
        "client_count": user.clients.count(),
        "project_count": user.projects.count(),
        "task_count": tasks.count(),
        "todo_count": tasks.filter(status=Task.Status.TODO).count(),
        "in_progress_count": tasks.filter(
            status=Task.Status.IN_PROGRESS
        ).count(),
        "done_count": tasks.filter(status=Task.Status.DONE).count(),
        "overdue_tasks": overdue_tasks,
        "recent_clients": user.clients.order_by("-created")[:5],
        "recent_projects": user.projects.order_by("-created")[:5],
        "recent_tasks": tasks.order_by("-created")[:5],
    }
    return render(request, "dashboard/dashboard.html", context)
