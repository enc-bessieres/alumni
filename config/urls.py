"""Adresses du site. Chaque application déclare les siennes dans son urls.py."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Connexion, déconnexion, mot de passe oublié… fournis par django-allauth.
    path("compte/", include("allauth.urls")),
    path("page/", include("pages_libres.urls")),
    path("", include("membres.urls")),  # /annuaire/ et /parametres/
    path("", include("accueil.urls")),
    path("blog/", include("blog.urls")),
    path("", include("gabarit.urls")),
]

# En développement seulement (DEBUG) : Django sert lui-même les fichiers envoyés.
# Sur le vrai serveur, static() ne renvoie rien : à décider sur l'issue #92.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
