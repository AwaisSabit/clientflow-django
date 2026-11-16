"""Project list, detail, create, update and delete views.

Every view needs a signed-in user. Every query is scoped to
owner=request.user, so a project that belongs to someone else simply
does not exist for this user — opening, editing or deleting it answers
with a 404, never a permission page and never the other user's data.
The client dropdown only offers the signed-in user's own clients, so
a project can never be attached to a client that belongs to someone else.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import Project


def _get_project(request, pk):
    """Fetch one of the signed-in user's projects, or 404."""
    return get_object_or_404(Project, pk=pk, owner=request.user)


@login_required
def project_list(request):
    """List the signed-in user's projects, ordered by name."""
    projects = (
        Project.objects.filter(owner=request.user)
        .select_related("client")
        .order_by("name")
    )
    return render(request, "projects/list.html", {"projects": projects})


@login_required
def project_detail(request, pk):
    project = _get_project(request, pk)
    return render(request, "projects/detail.html", {"project": project})


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, f"Project {project.name} added.")
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(user=request.user)
    return render(request, "projects/form.html", {"form": form})


@login_required
def project_update(request, pk):
    project = _get_project(request, pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Project {project.name} updated.")
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project, user=request.user)
    return render(
        request, "projects/form.html", {"form": form, "project": project}
    )


@login_required
def project_delete(request, pk):
    project = _get_project(request, pk)
    if request.method == "POST":
        name = project.name
        project.delete()
        messages.success(request, f"Project {name} deleted.")
        return redirect("projects:list")
    return render(
        request, "projects/confirm_delete.html", {"project": project}
    )
