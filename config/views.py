"""Home and health-check views for ClientFlow (Day 1)."""
from django.http import JsonResponse
from django.shortcuts import render


def home(request):
    """Landing page: what ClientFlow is and where it is heading."""
    return render(request, "home.html")


def health(request):
    """Simple health endpoint used by the smoke test (and later by monitoring)."""
    return JsonResponse({"status": "ok", "app": "clientflow"})
