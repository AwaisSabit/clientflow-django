"""Dashboard view for ClientFlow.

One page that sums up the signed-in user's own work: how many clients,
projects and tasks they have, how their tasks split by status, which
tasks are overdue, and their newest items. Everything is filtered on
owner=request.user, so another user's counts or items never appear here.

The task counts come from a single aggregate query instead of one
count per status, and the task lists fetch their project in the same
query, so the page loads in a fixed number of queries no matter how
many tasks the user has.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from apps.tasks.models import Task


@login_required
def dashboard(request):
    """Show the signed-in user's own counts, overdue tasks and recent items."""
    user = request.user
    tasks = user.tasks.all()
    task_counts = tasks.aggregate(
        total=Count("pk"),
        todo=Count("pk", filter=Q(status=Task.Status.TODO)),
        in_progress=Count(
            "pk", filter=Q(status=Task.Status.IN_PROGRESS)
        ),
        done=Count("pk", filter=Q(status=Task.Status.DONE)),
    )
    overdue_tasks = (
        tasks.filter(due_date__lt=timezone.localdate())
        .exclude(status=Task.Status.DONE)
        .select_related("project")
        .order_by("due_date")
    )
    context = {
        "client_count": user.clients.count(),
        "project_count": user.projects.count(),
        "task_count": task_counts["total"],
        "todo_count": task_counts["todo"],
        "in_progress_count": task_counts["in_progress"],
        "done_count": task_counts["done"],
        "overdue_tasks": overdue_tasks,
        "recent_clients": user.clients.order_by("-created")[:5],
        "recent_projects": user.projects.order_by("-created")[:5],
        "recent_tasks": tasks.select_related("project").order_by(
            "-created"
        )[:5],
    }
    return render(request, "dashboard/dashboard.html", context)
