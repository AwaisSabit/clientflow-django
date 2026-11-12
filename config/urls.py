"""ClientFlow URL configuration."""
from django.contrib import admin
from django.urls import path

from config.views import health, home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("health/", health, name="health"),
]
