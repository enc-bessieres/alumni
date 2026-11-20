"""
Droits d'accès du projet — LE SEUL ENDROIT où ils sont définis (règle 3 d'AGENTS.md).

On utilise uniquement le mécanisme de Django : des permissions regroupées dans des groupes.
Le rôle d'un membre, c'est la liste de ses groupes. On le donne dans le back-office, sur la
fiche du membre (champ « Groupes »), en cochant aussi « accès au back-office ».

Les vues et le back-office se contentent de demander une permission (`has_perm`,
`@permission_required`) : ils ne décident jamais eux-mêmes qui a le droit.

À chaque `migrate`, les permissions de ces groupes sont remises exactement à la liste
ci-dessous : une permission ajoutée ou retirée à la main dans le back-office est écrasée.
Pour changer un rôle durablement, on modifie GROUPES, dans une PR.

Pour un autre domaine (référentiels, pages libres…) : ajouter ses permissions ici, dans sa PR.
"""

import warnings
from functools import wraps

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Membre

# Groupe -> permissions accordées ("application.code_de_la_permission").
GROUPES = {
    # Valide ou refuse les inscriptions depuis le back-office.
    "Validateur": [
        "membres.view_membre",
        "membres.change_membre",
        "membres.valider_inscription",
    ],
    # Gère les comptes, et donne ou retire les groupes.
    "Administrateur": [
        "membres.view_membre",
        "membres.add_membre",
        "membres.change_membre",
        "membres.delete_membre",
        "membres.valider_inscription",
        "membres.gerer_les_droits",
        # Référentiels (#18) : sites, niveaux et diplômes.
        "referentiels.view_site",
        "referentiels.add_site",
        "referentiels.change_site",
        "referentiels.delete_site",
        "referentiels.view_niveau",
        "referentiels.add_niveau",
        "referentiels.change_niveau",
        "referentiels.delete_niveau",
        "referentiels.view_diplome",
        "referentiels.add_diplome",
        "referentiels.change_diplome",
        "referentiels.delete_diplome",
        # Parcours des membres (#31).
        "referentiels.view_formation",
        "referentiels.add_formation",
        "referentiels.change_formation",
        "referentiels.delete_formation",
        # Pages libres (#23) : mentions légales, CGU…
        "pages_libres.view_page",
        "pages_libres.add_page",
        "pages_libres.change_page",
        "pages_libres.delete_page",
    ],
}


def permissions(codes):
    """Les objets Permission de Django correspondant à une liste "application.code"."""
    trouvees = []
    for code in codes:
        app_label, codename = code.split(".")
        trouvees += Permission.objects.filter(content_type__app_label=app_label, codename=codename)
    return trouvees


def codes_inconnus(codes):
    """Les codes de GROUPES qui ne désignent aucune permission existante."""
    return [code for code in sorted(codes) if not permissions([code])]


def derniere_application():
    """La dernière application à recevoir le signal post_migrate (celles qui ont des modèles)."""
    return [config for config in apps.get_app_configs() if config.models_module][-1]


def creer_groupes(app_config=None, **kwargs):
    """
    Crée ou met à jour les groupes après `migrate` (signal post_migrate, envoyé une fois par
    application). Django crée les permissions application par application : tant qu'elles
    n'existent pas toutes, on attend le signal suivant.

    Au dernier signal, toutes les permissions existent : un code encore introuvable est une
    faute de frappe, et on le signale. Avant, on ne dit rien : sur une base existante, la
    permission d'un nouveau modèle n'est pas encore créée, ce ne serait pas une erreur.
    """
    tous_les_codes = {code for codes in GROUPES.values() for code in codes}
    if app_config is None or app_config == derniere_application():
        for code in codes_inconnus(tous_les_codes):
            warnings.warn(
                f"membres/droits.py : la permission « {code} » n'existe pas (faute de frappe ?). "
                "Les groupes ne sont pas mis à jour.",
                stacklevel=2,
            )
    if len(permissions(tous_les_codes)) < len(tous_les_codes):
        return
    for nom, codes in GROUPES.items():
        groupe, _ = Group.objects.get_or_create(name=nom)
        groupe.permissions.set(permissions(codes))


def peut_modifier_le_compte(utilisateur, membre):
    """
    Peut-on modifier ou supprimer ce compte (y compris le statut de son inscription) ?
    - le compte d'un superutilisateur : seulement un superutilisateur ;
    - le compte d'un membre de l'équipe (accès au back-office ou au moins un groupe) :
      seulement avec « gerer_les_droits ». Sinon un validateur pourrait refuser l'inscription
      d'un administrateur, qui ne pourrait plus se connecter.
    """
    if membre.is_superuser:
        return utilisateur.is_superuser
    if membre.is_staff or membre.groups.exists():
        return utilisateur.has_perm("membres.gerer_les_droits")
    return True


def peut_gerer_le_compte(utilisateur, membre=None):
    """
    Peut-on modifier l'identité, l'e-mail, le mot de passe ou les droits de ce compte ?
    Il faut la permission « gerer_les_droits » (groupe Administrateur) : un validateur ne fait
    que valider les inscriptions. Changer l'e-mail ou le mot de passe d'un compte, c'est
    pouvoir s'en emparer.
    """
    if membre is not None and not peut_modifier_le_compte(utilisateur, membre):
        return False
    return utilisateur.has_perm("membres.gerer_les_droits")


def est_membre_valide(utilisateur):
    """
    Peut-on voir ce qui est réservé aux membres (annuaire, puis profils) ? Il faut être
    connecté, avec un compte actif et une inscription validée (décision de l'issue #9).
    """
    return (
        utilisateur.is_authenticated
        and utilisateur.is_active
        and utilisateur.statut_inscription == Membre.StatutInscription.VALIDEE
    )


def reserve_aux_membres_valides(vue):
    """
    Décorateur des vues réservées aux membres validés :
    - visiteur non connecté : page de connexion, puis retour à la page demandée ;
    - connecté mais pas validé (inscription refusée après sa connexion…) : page 403.
    """

    @wraps(vue)
    def vue_protegee(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not est_membre_valide(request.user):
            raise PermissionDenied
        return vue(request, *args, **kwargs)

    return vue_protegee
