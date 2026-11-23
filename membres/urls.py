from django.urls import path

from . import views

app_name = "membres"

urlpatterns = [
    path("annuaire/", views.annuaire, name="annuaire"),
    path("annuaire/<int:pk>/", views.fiche, name="fiche"),
    path("parametres/", views.parametres, name="parametres"),
    path("profil/", views.profil, name="profil"),
]
