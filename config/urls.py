"""Adresses du site. Chaque application déclare les siennes dans son urls.py."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Connexion, déconnexion, mot de passe oublié… fournis par django-allauth.
    path("compte/", include("allauth.urls")),
    path("page/", include("pages_libres.urls")),
    path("annuaire/", include("membres.urls")),
    # Avant gabarit : /mentorat/ reste la page provisoire, ses sous-pages viennent d'ici.
    path("mentorat/", include("mentorat.urls")),
    path("", include("accueil.urls")),
    path("", include("gabarit.urls")),
]
