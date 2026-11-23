from django.urls import path

from . import views

app_name = "membres"

urlpatterns = [
    path("annuaire/", views.annuaire, name="annuaire"),
    path("parametres/", views.parametres, name="parametres"),
]
