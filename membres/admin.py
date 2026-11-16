from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Membre

# Champs qui donnent des droits : seul un compte qui a « gerer_les_droits » peut les modifier.
CHAMPS_DES_DROITS = ["is_staff", "groups", "user_permissions"]


@admin.register(Membre)
class MembreAdmin(UserAdmin):
    """Back-office des membres, fourni par Django. On ne fait que choisir les champs affichés."""

    list_display = ["nom", "prenom", "email", "categorie", "statut_inscription", "is_staff"]
    list_filter = ["statut_inscription", "categorie", "groups", "is_staff"]
    search_fields = ["nom", "prenom", "nom_de_naissance", "email"]
    ordering = ["nom", "prenom"]
    readonly_fields = ["legacy_id", "last_login", "cree_le"]
    filter_horizontal = ["groups", "user_permissions"]

    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        (
            "Identité",
            {"fields": ["civilite", "prenom", "nom", "nom_de_naissance", "categorie"]},
        ),
        ("Inscription", {"fields": ["statut_inscription", "is_active"]}),
        # Le rôle = les groupes (Validateur, Administrateur), définis dans membres/droits.py.
        ("Rôle et droits", {"fields": ["groups", "is_staff", "is_superuser", "user_permissions"]}),
        ("Suivi", {"fields": ["legacy_id", "cree_le", "last_login"]}),
    ]
    add_fieldsets = [
        (
            None,
            {"fields": ["email", "prenom", "nom", "categorie", "password1", "password2"]},
        ),
    ]

    def get_readonly_fields(self, request, obj=None):
        # Sans ces verrous, un validateur (qui peut modifier une fiche pour valider une
        # inscription) pourrait s'ajouter lui-même au groupe Administrateur.
        champs = list(super().get_readonly_fields(request, obj))
        if not request.user.has_perm("membres.valider_inscription"):
            champs.append("statut_inscription")
        if not request.user.has_perm("membres.gerer_les_droits"):
            champs += CHAMPS_DES_DROITS
        if not request.user.is_superuser:
            champs.append("is_superuser")
        return champs
