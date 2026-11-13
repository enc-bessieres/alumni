"""Le menu du site, défini à un seul endroit.

Le gabarit l'affiche deux fois : dans la colonne de gauche sur ordinateur,
et dans la barre du bas sur mobile (les 4 premières entrées, puis « Plus »).

Quand un domaine livre sa vraie page, il remplace ici le nom d'adresse
provisoire (par exemple « gabarit:annuaire ») par le sien.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Entree:
    libelle: str
    nom_url: str


MENU = [
    Entree("Accueil", "accueil:index"),
    Entree("Annuaire", "gabarit:annuaire"),
    Entree("Mentorat", "gabarit:mentorat"),
    Entree("Groupes", "gabarit:groupes"),
    Entree("Actualités", "gabarit:actualites"),
    Entree("Événements", "gabarit:evenements"),
    Entree("Emplois & stages", "gabarit:emplois"),
    Entree("Ressources", "gabarit:ressources"),
]

# Nombre d'entrées dans la barre du bas sur mobile ; les autres vont dans « Plus ».
NB_ENTREES_MOBILE = 4


@dataclass(frozen=True)
class LienDuPied:
    libelle: str
    slug: str


# Liens du pied de page vers les pages libres de Marie-Dominique (issue #12).
# Chaque slug est celui d'une page créée par sa migration « pages de départ ».
PIED_DE_PAGE = [
    LienDuPied("À propos", "a-propos"),
    LienDuPied("Mentions légales", "mentions-legales"),
    LienDuPied("CGU", "cgu"),
    LienDuPied("Politique de confidentialité", "confidentialite"),
    LienDuPied("Charte du mentorat", "charte-du-mentorat"),
]
