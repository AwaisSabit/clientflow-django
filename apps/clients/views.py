"""Client list, detail, create, update and delete views.

Every view needs a signed-in user. Every query is scoped to
owner=request.user, so a client that belongs to someone else simply
does not exist for this user — opening, editing or deleting it answers
with a 404, never a permission page and never the other user's data.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client

CLIENTS_PER_PAGE = 10


def _get_client(request, pk):
    """Fetch one of the signed-in user's clients, or 404."""
    return get_object_or_404(Client, pk=pk, owner=request.user)


@login_required
def client_list(request):
    """List the signed-in user's clients, with search, company filter
    and pagination.

    `q` searches name, company and email (case-insensitive); `company`
    narrows the list to one company. Both filters only ever see the
    signed-in user's own clients, and the page links keep them.
    """
    own_clients = Client.objects.filter(owner=request.user)
    search_query = request.GET.get("q", "").strip()
    company_filter = request.GET.get("company", "").strip()

    clients = own_clients.order_by("name")
    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query)
            | Q(company__icontains=search_query)
            | Q(email__icontains=search_query)
        )
    if company_filter:
        clients = clients.filter(company=company_filter)

    companies = (
        own_clients.exclude(company="")
        .values_list("company", flat=True)
        .distinct()
        .order_by("company")
    )

    paginator = Paginator(clients, CLIENTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # The page links need the current search and filter, but not the
    # page number itself.
    kept_params = request.GET.copy()
    kept_params.pop("page", None)
    query_string = kept_params.urlencode()

    return render(
        request,
        "clients/list.html",
        {
            "clients": page_obj,
            "page_obj": page_obj,
            "has_clients": own_clients.exists(),
            "total_count": paginator.count,
            "search_query": search_query,
            "company_filter": company_filter,
            "companies": companies,
            "query_string": query_string,
        },
    )


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
