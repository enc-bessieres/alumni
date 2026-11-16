"""
Droits d'accès du projet — LE SEUL ENDROIT où ils sont définis (règle 3 d'AGENTS.md).

On utilise uniquement le mécanisme de Django : des permissions regroupées dans des groupes.
Le rôle d'un membre, c'est la liste de ses groupes. On le donne dans le back-office, sur la
fiche du membre (champ « Groupes »), en cochant aussi « accès au back-office ».

Les vues et le back-office se contentent de demander une permission (`has_perm`,
`@permission_required`) : ils ne décident jamais eux-mêmes qui a le droit.

Pour un autre domaine (référentiels, pages libres…) : ajouter ses permissions ici, dans sa PR.
"""

from django.contrib.auth.models import Group, Permission

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
    ],
}


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
