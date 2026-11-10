from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Membre


@admin.register(Membre)
class MembreAdmin(UserAdmin):
    """Back-office des membres, fourni par Django. On ne fait que choisir les champs affichés."""

    list_display = ["nom", "prenom", "email", "categorie", "statut_inscription", "role"]
    list_filter = ["statut_inscription", "categorie", "role"]
    search_fields = ["nom", "prenom", "nom_de_naissance", "email"]
    ordering = ["nom", "prenom"]
    readonly_fields = ["legacy_id", "last_login", "cree_le"]

    # Pas de groupes ni de permissions à la main : ils découlent du rôle (membres/droits.py).
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        (
            "Identité",
            {"fields": ["civilite", "prenom", "nom", "nom_de_naissance", "categorie"]},
        ),
        ("Inscription et rôle", {"fields": ["statut_inscription", "role", "is_active"]}),
        ("Suivi", {"fields": ["legacy_id", "cree_le", "last_login"]}),
    ]
    add_fieldsets = [
        (
            None,
            {"fields": ["email", "prenom", "nom", "categorie", "password1", "password2"]},
        ),
    ]

    def get_readonly_fields(self, request, obj=None):
        # Les permissions viennent de membres/droits.py ; ici on les applique seulement.
        champs = list(super().get_readonly_fields(request, obj))
        if not request.user.has_perm("membres.changer_role"):
            champs.append("role")
        if not request.user.has_perm("membres.valider_inscription"):
            champs.append("statut_inscription")
        return champs
