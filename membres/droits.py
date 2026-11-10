"""
Droits d'accès du projet — LE SEUL ENDROIT où ils sont définis (règle 3 d'AGENTS.md).

On utilise le mécanisme de Django : des permissions regroupées dans des groupes.
Chaque membre reçoit automatiquement les groupes qui correspondent à son statut et à son rôle.
Les vues et le back-office se contentent ensuite de demander une permission
(`@permission_required`, `has_perm`) : ils ne décident jamais eux-mêmes qui a le droit.

Pour un autre domaine (messagerie, articles…) : ajouter ses permissions ici, dans sa propre PR.
"""

from django.contrib.auth.models import Group, Permission

# Groupe -> permissions accordées ("application.code_de_la_permission").
GROUPES = {
    # Tout membre dont l'inscription est validée.
    "Membre": [
        "membres.consulter_annuaire",
    ],
    # Valide ou refuse les inscriptions depuis le back-office.
    "Validateur": [
        "membres.view_membre",
        "membres.change_membre",
        "membres.valider_inscription",
    ],
    # Gère les comptes et les rôles.
    "Administrateur": [
        "membres.view_membre",
        "membres.add_membre",
        "membres.change_membre",
        "membres.delete_membre",
        "membres.valider_inscription",
        "membres.changer_role",
    ],
}


def groupes_du_membre(membre):
    """Les groupes qu'un membre doit avoir, d'après le statut de son inscription et son rôle."""
    groupes = []
    if membre.statut_inscription == membre.StatutInscription.VALIDEE:
        groupes.append("Membre")
    if membre.role == membre.Role.VALIDATEUR:
        groupes.append("Validateur")
    if membre.role == membre.Role.ADMINISTRATEUR:
        groupes.append("Administrateur")
    return groupes


def permissions(codes):
    """Les objets Permission de Django correspondant à une liste "application.code"."""
    trouvees = []
    for code in codes:
        app_label, codename = code.split(".")
        trouvees += Permission.objects.filter(content_type__app_label=app_label, codename=codename)
    return trouvees


def creer_groupes(**kwargs):
    """
    Crée ou met à jour les groupes après `migrate` (signal post_migrate).
    Django crée les permissions application par application : tant qu'elles n'existent
    pas toutes, on attend le signal suivant.
    """
    tous_les_codes = {code for codes in GROUPES.values() for code in codes}
    if len(permissions(tous_les_codes)) < len(tous_les_codes):
        return
    for nom, codes in GROUPES.items():
        groupe, _ = Group.objects.get_or_create(name=nom)
        groupe.permissions.set(permissions(codes))


def appliquer_groupes(sender, instance, **kwargs):
    """Après chaque enregistrement d'un membre (signal post_save), on aligne ses groupes."""
    instance.groups.set(Group.objects.filter(name__in=groupes_du_membre(instance)))
