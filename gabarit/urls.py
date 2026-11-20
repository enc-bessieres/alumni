"""Pages provisoires « Bientôt disponible ».

Quand un domaine livre sa vraie page, il supprime sa ligne ici,
déclare ses adresses dans sa propre application et met à jour gabarit/menu.py.
"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "gabarit"

urlpatterns = [
    path("mentorat/", views.bientot, {"titre": "Mentorat"}, name="mentorat"),
    path("groupes/", views.bientot, {"titre": "Groupes"}, name="groupes"),
    path("actualites/", views.bientot, {"titre": "Actualités"}, name="actualites"),
    path("evenements/", views.bientot, {"titre": "Événements"}, name="evenements"),
    path("emplois/", views.bientot, {"titre": "Emplois & stages"}, name="emplois"),
    path("ressources/", views.bientot, {"titre": "Ressources"}, name="ressources"),
    # Réservées aux membres connectés (règle 3), même tant qu'elles sont vides.
    path("profil/", login_required(views.bientot), {"titre": "Profil"}, name="profil"),
    path(
        "parametres/",
        login_required(views.bientot),
        {"titre": "Paramètres"},
        name="parametres",
    ),
]
