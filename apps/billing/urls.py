"""URLs for the billing app: invoice list, create, detail, edit and delete."""
from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("add/", views.invoice_create, name="create"),
    path("export/", views.invoice_export_csv, name="export"),
    path("<int:pk>/", views.invoice_detail, name="detail"),
    path("<int:pk>/edit/", views.invoice_update, name="update"),
    path("<int:pk>/delete/", views.invoice_delete, name="delete"),
    path("<int:pk>/status/", views.invoice_status_change, name="status"),
]
