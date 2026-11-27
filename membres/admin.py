from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied

from .droits import peut_gerer_le_compte, peut_modifier_le_compte
from .models import Membre

# Ce qu'un validateur ne peut pas modifier : il ne touche qu'au statut de l'inscription.
CHAMPS_DU_COMPTE = [
    "email",
    "civilite",
    "prenom",
    "nom",
    "nom_de_naissance",
    "categorie",
    "is_active",
    "is_staff",
    "groups",
]
# Réservés aux superutilisateurs : un administrateur donne des groupes, pas des permissions.
CHAMPS_DU_SUPERUTILISATEUR = ["is_superuser", "user_permissions"]


@admin.register(Membre)
class MembreAdmin(UserAdmin):
    """
    Back-office des membres, fourni par Django. On choisit les champs affichés, et on applique
    les règles de membres/droits.py : on ne décide pas ici qui a le droit.
    """

    list_display = [
        "nom",
        "prenom",
        "email",
        "categorie",
        "statut_inscription",
        "compte_active",
        "cree_le",
        "is_staff",
    ]
    # Les validateurs trouvent les inscriptions à valider avec les filtres « statut » (en attente)
    # et « créé le » (par exemple les 7 derniers jours) : décision 0005.
    list_filter = [
        "statut_inscription",
        "compte_active",
        "cree_le",
        "categorie",
        "groups",
        "is_staff",
    ]
    search_fields = ["nom", "prenom", "nom_de_naissance", "email"]
    ordering = ["nom", "prenom"]
    # Les choix du membre (annuaire, e-mail, LinkedIn) : l'équipe les voit, sans les changer.
    # compte_active aussi : c'est la première connexion du membre qui l'active (#85).
    readonly_fields = [
        "legacy_id",
        "compte_active",
        "last_login",
        "cree_le",
        "visible_dans_annuaire",
        "email_visible",
        "linkedin",
    ]
    filter_horizontal = ["groups", "user_permissions"]

    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        (
            "Identité",
            {"fields": ["civilite", "prenom", "nom", "nom_de_naissance", "categorie"]},
        ),
        ("Inscription", {"fields": ["statut_inscription", "compte_active", "is_active"]}),
        # Les choix du membre (Paramètres) : l'équipe les voit, mais ne les change pas.
        ("Annuaire et fiche", {"fields": ["visible_dans_annuaire", "email_visible", "linkedin"]}),
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

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None or peut_gerer_le_compte(request.user, obj):
            return fieldsets
        # Sans ce droit, ni l'empreinte du mot de passe ni le lien pour le changer.
        return [
            (titre, {**options, "fields": [c for c in options["fields"] if c != "password"]})
            for titre, options in fieldsets
        ]

    def get_readonly_fields(self, request, obj=None):
        champs = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            champs += CHAMPS_DU_SUPERUTILISATEUR
        if not peut_gerer_le_compte(request.user, obj):
            champs += CHAMPS_DU_COMPTE
        if not request.user.has_perm("membres.valider_inscription"):
            champs.append("statut_inscription")
        return list(dict.fromkeys(champs))  # sans doublon

    def has_change_permission(self, request, obj=None):
        if obj is not None and not peut_modifier_le_compte(request.user, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Django la vérifie aussi pour chaque ligne de la suppression en masse.
        if obj is not None and not peut_modifier_le_compte(request.user, obj):
            return False
        return super().has_delete_permission(request, obj)

    def user_change_password(self, request, id, form_url=""):
        membre = self.get_object(request, unquote(id))
        if membre is not None and not peut_gerer_le_compte(request.user, membre):
            raise PermissionDenied
        return super().user_change_password(request, id, form_url)
