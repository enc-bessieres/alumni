"""
Import de l'annuaire Datalumni (`directory.csv`) : un compte par ligne (issue #84).

Le format est celui des exports réels (docs/migration/export-reel.md). Un membre est retrouvé
par son identifiant Datalumni (`user_id` → `legacy_id`) : relancer l'import ne crée pas de
doublon, il remet à jour ce que l'export contient.

Datalumni ne fournit pas les mots de passe : chaque compte est créé sans mot de passe
utilisable, et le membre définit le sien par un lien reçu par e-mail (#85).

Le résumé liste les comptes ignorés, par identifiant Datalumni seulement (jamais de nom ni
d'e-mail : ce sont des données réelles).
"""

import csv
from dataclasses import dataclass, field
from datetime import UTC, datetime

from allauth.account.models import EmailAddress
from django.db import transaction

from datalumni.export_factice import COLONNES
from membres.models import Membre

# Sépare deux valeurs dans `category`, `campus` et `degree` seulement : certains secteurs
# contiennent eux-mêmes « / » (« Conseil / Audit »).
SEPARATEUR = " / "
CATEGORIES = {
    "Alumni": Membre.Categorie.ALUMNI,
    "Étudiant": Membre.Categorie.ETUDIANT,
    "Enseignant": Membre.Categorie.ENSEIGNANT,
    "Équipe administrative": Membre.Categorie.ADMINISTRATIF,
    "Candidat": Membre.Categorie.CANDIDAT,
    "Recruteur": Membre.Categorie.RECRUTEUR,
}
# Les 5 écritures de Datalumni ; « Non renseigné » devient vide.
CIVILITES = {
    "Mme.": Membre.Civilite.MADAME,
    "Madame": Membre.Civilite.MADAME,
    "M.": Membre.Civilite.MONSIEUR,
    "Monsieur": Membre.Civilite.MONSIEUR,
    "Non renseigné": "",
    "": "",
}


class FormatInattendu(Exception):
    """Le fichier n'a pas les colonnes de directory.csv : on n'importe rien."""


class CompteIgnore(Exception):
    """Une ligne qu'on ne peut pas importer telle quelle : elle est signalée, pas créée."""


@dataclass
class Resume:
    crees: int = 0
    mis_a_jour: int = 0
    # (identifiant Datalumni, raison) : comptes non importés.
    ignores: list = field(default_factory=list)


def lire_csv(chemin):
    """Les lignes de directory.csv (UTF-8 avec BOM), en dictionnaires. Vérifie les colonnes."""
    with open(chemin, encoding="utf-8-sig", newline="") as fichier:
        lecteur = csv.DictReader(fichier)
        manquantes = [c for c in COLONNES if c not in (lecteur.fieldnames or [])]
        if manquantes:
            raise FormatInattendu(f"colonnes manquantes : {', '.join(manquantes)}")
        return list(lecteur)


def moment(texte):
    """« 2025-04-14T09:12:47+00:00 » ou « 2026-06-24 » → une date avec fuseau ; vide → None."""
    if not texte:
        return None
    valeur = datetime.fromisoformat(texte)
    return valeur if valeur.tzinfo else valeur.replace(tzinfo=UTC)


def champs_du_membre(ligne):
    """Les champs du Membre tirés d'une ligne. Lève CompteIgnore si c'est impossible."""
    if not ligne["email"]:
        raise CompteIgnore("pas d'adresse e-mail (elle est obligatoire)")

    # Deux catégories (12 comptes) : la première est gardée (à confirmer par M. Robert, #84).
    categories = ligne["category"].split(SEPARATEUR) if ligne["category"] else []
    if categories and categories[0] not in CATEGORIES:
        raise CompteIgnore(f"catégorie inconnue : {categories[0]}")

    return {
        "email": Membre.objects.normalize_email(ligne["email"]),
        "civilite": CIVILITES.get(ligne["civility"], ""),
        # Les noms sont gardés tels quels, en majuscules (à confirmer par M. Robert, #84) :
        # une conversion automatique se tromperait sur les particules et les noms composés.
        "prenom": ligne["first_name"],
        "nom": ligne["last_name"],
        "nom_de_naissance": ligne["birth_name"],
        "categorie": CATEGORIES[categories[0]] if categories else "",
        # Toujours True chez Datalumni ; une case vide suit la même règle.
        "visible_dans_annuaire": ligne["visibility_directory"] != "False",
        "last_login": moment(ligne["last_login"]),
    }


@transaction.atomic  # tout ou rien : une erreur à la 3000e ligne n'en laisse pas 2999 en base
def importer(lignes):
    """Crée ou met à jour un membre par ligne de directory.csv. Renvoie le Resume."""
    resume = Resume()
    # Chargés une fois pour toutes, plutôt qu'une requête par ligne : 6138 lignes.
    par_legacy_id = {str(m.legacy_id): m for m in Membre.objects.exclude(legacy_id=None)}
    proprietaire = {e.lower(): str(i) for e, i in Membre.objects.values_list("email", "legacy_id")}
    adresses = {a.user_id: a for a in EmailAddress.objects.filter(primary=True)}

    for ligne in lignes:
        identifiant = ligne["user_id"]
        try:
            champs = champs_du_membre(ligne)
        except CompteIgnore as raison:
            resume.ignores.append((identifiant, str(raison)))
            continue
        # Une adresse déjà prise par un autre compte (inscrit sur le nouveau site, ou autre
        # ligne de l'export) : on ne touche pas à ce compte. À trancher à la main.
        if proprietaire.get(champs["email"], identifiant) != identifiant:
            resume.ignores.append((identifiant, "adresse e-mail déjà utilisée par un autre compte"))
            continue

        membre = par_legacy_id.get(identifiant)
        if membre is None:
            membre = Membre(
                legacy_id=identifiant,
                # Un compte activé chez Datalumni est considéré comme validé (export-reel.md).
                statut_inscription=Membre.StatutInscription.VALIDEE,
            )
            # Pas de mot de passe chez Datalumni. Fixé à la création seulement : une relance
            # ne retire jamais le mot de passe qu'un membre a défini sur le nouveau site.
            membre.set_unusable_password()
            if creation := moment(ligne["import_date"]) or moment(ligne["account_activation_date"]):
                membre.cree_le = creation
            resume.crees += 1
        else:
            resume.mis_a_jour += 1
        for nom, valeur in champs.items():
            setattr(membre, nom, valeur)
        membre.save()
        proprietaire[membre.email] = identifiant

        # L'adresse vue par django-allauth. Non vérifiée : elle le sera quand le membre
        # définira son mot de passe par le lien reçu à cette adresse (#85).
        adresse = adresses.get(membre.pk)
        if adresse is None:
            EmailAddress.objects.create(user=membre, email=membre.email, primary=True)
        elif adresse.email != membre.email:
            adresse.email, adresse.verified = membre.email, False
            adresse.save()

    return resume
