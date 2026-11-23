"""
Import des membres de Datalumni et de leurs comptes (issue #37).

Lit l'export au format décrit dans docs/migration/export-factice.md et crée, ou met à jour,
un Membre par personne. Un membre est retrouvé par son identifiant Datalumni (legacy_id) :
relancer l'import ne crée pas de doublon, il remet les comptes à jour.

Les diplômes et promos sont importés à part (#38). Les photos, expériences et villes
attendent les champs du profil ; les liaisons Google et LinkedIn, les applications de l'ENC.
"""

from dataclasses import dataclass, field
from datetime import datetime

from allauth.account.models import EmailAddress
from django.db import transaction

from membres.models import Membre

CATEGORIES = {
    "Alumni": Membre.Categorie.ALUMNI,
    "Étudiant": Membre.Categorie.ETUDIANT,
    "Enseignant": Membre.Categorie.ENSEIGNANT,
    "Équipe administrative": Membre.Categorie.ADMINISTRATIF,
    "Candidat": Membre.Categorie.CANDIDAT,
    "Recruteur": Membre.Categorie.RECRUTEUR,
}
STATUTS = {
    "accepte": Membre.StatutInscription.VALIDEE,
    "en_attente": Membre.StatutInscription.EN_ATTENTE,
    "refuse": Membre.StatutInscription.REFUSEE,
}
CIVILITES = {"M.": Membre.Civilite.MONSIEUR, "Mme": Membre.Civilite.MADAME}


class CompteIgnore(Exception):
    """Un compte qu'on ne peut pas importer tel quel : il est signalé, pas créé."""


@dataclass
class Resume:
    crees: int = 0
    mis_a_jour: int = 0
    # (identifiant Datalumni, raison) : jamais de nom ni d'e-mail, ce sont des données réelles.
    ignores: list = field(default_factory=list)


def date(texte):
    """« 2025-04-14T09:12:47Z » → une date avec fuseau ; None reste None."""
    return datetime.fromisoformat(texte) if texte else None


def champs_du_membre(donnees):
    """Les champs du Membre, à partir d'un membre de l'export. Lève CompteIgnore si impossible."""
    if not donnees["email"]:
        raise CompteIgnore("pas d'adresse e-mail (elle est obligatoire)")
    if donnees["categorie"] not in CATEGORIES:
        raise CompteIgnore(f"catégorie inconnue : {donnees['categorie']}")
    if donnees["statut"] not in STATUTS:
        raise CompteIgnore(f"statut inconnu : {donnees['statut']}")
    identite = donnees["metadata"]
    return {
        "email": donnees["email"],
        # Le même format que Django (pbkdf2_sha256) : l'ancien mot de passe continue de marcher.
        # Une empreinte qui commence par « ! » est inutilisable : le membre passera par
        # « mot de passe oublié ».
        "password": donnees["password"],
        "civilite": CIVILITES.get(identite["civilite"], ""),
        "prenom": identite["prenom"],
        "nom": identite["nom"],
        "nom_de_naissance": identite["nom_naissance"] or "",
        "categorie": CATEGORIES[donnees["categorie"]],
        "statut_inscription": STATUTS[donnees["statut"]],
        "visible_dans_annuaire": donnees["visible_annuaire"],
        "cree_le": date(donnees["date_inscription"]),
        "last_login": date(donnees["derniere_connexion"]),
    }


def importer_un_membre(donnees):
    """Crée ou met à jour un membre et son adresse. Renvoie True s'il vient d'être créé."""
    champs = champs_du_membre(donnees)
    # Une adresse déjà prise par un autre compte (inscrit sur le nouveau site, ou autre membre
    # Datalumni) : on ne touche pas à ce compte. À trancher à la main.
    deja_prise = Membre.objects.filter(email__iexact=champs["email"]).exclude(
        legacy_id=donnees["uuid"]
    )
    if deja_prise.exists():
        raise CompteIgnore("adresse e-mail déjà utilisée par un autre compte")

    membre, cree = Membre.objects.update_or_create(legacy_id=donnees["uuid"], defaults=champs)
    # L'adresse vue par django-allauth : vérifiée ou non, comme chez Datalumni.
    EmailAddress.objects.filter(user=membre).exclude(email=membre.email).delete()
    EmailAddress.objects.update_or_create(
        user=membre,
        email=membre.email,
        defaults={"verified": donnees["email_verifie"], "primary": True},
    )
    return cree


@transaction.atomic  # tout ou rien : une erreur au 600ᵉ membre n'en laisse pas 599 en base
def importer(export):
    """Importe les membres d'un export (dictionnaire déjà lu depuis le JSON)."""
    resume = Resume()
    for donnees in export["membres"]:
        try:
            if importer_un_membre(donnees):
                resume.crees += 1
            else:
                resume.mis_a_jour += 1
        except CompteIgnore as raison:
            resume.ignores.append((donnees["uuid"], str(raison)))
    return resume
