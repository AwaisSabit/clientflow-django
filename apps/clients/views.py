"""Client list, detail, create, update and delete views.

Every view needs a signed-in user. Every query is scoped to
owner=request.user, so a client that belongs to someone else simply
does not exist for this user — opening, editing or deleting it answers
with a 404, never a permission page and never the other user's data.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client


def _get_client(request, pk):
    """Fetch one of the signed-in user's clients, or 404."""
    return get_object_or_404(Client, pk=pk, owner=request.user)


@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user).order_by("name")
    return render(request, "clients/list.html", {"clients": clients})


@login_required
def client_detail(request, pk):
    client = _get_client(request, pk)
    return render(request, "clients/detail.html", {"client": client})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user
            client.save()
            messages.success(request, f"Client {client.name} added.")
            return redirect("clients:detail", pk=client.pk)
    else:
        form = ClientForm()
    return render(request, "clients/form.html", {"form": form})


@login_required
def client_update(request, pk):
    client = _get_client(request, pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client {client.name} updated.")
            return redirect("clients:detail", pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(
        request, "clients/form.html", {"form": form, "client": client}
    )


@login_required
def client_delete(request, pk):
    client = _get_client(request, pk)
    if request.method == "POST":
        name = client.name
        client.delete()
        messages.success(request, f"Client {name} deleted.")
        return redirect("clients:list")
    return render(request, "clients/confirm_delete.html", {"client": client})
