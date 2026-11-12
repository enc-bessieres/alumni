"""Adresses du site. Chaque application déclare les siennes dans son urls.py."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("pages/", include("pages_libres.urls")),
    path("", include("accueil.urls")),
]
