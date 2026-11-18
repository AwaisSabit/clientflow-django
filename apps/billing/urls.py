"""URLs for the billing app: invoice list, create and detail."""
from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("add/", views.invoice_create, name="create"),
    path("<int:pk>/", views.invoice_detail, name="detail"),
]
