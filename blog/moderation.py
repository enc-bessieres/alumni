"""
Liste noire des mots interdits dans les articles (décision de #43).

La recherche ignore les majuscules et les accents, et ne cherche que des mots entiers :
un mot interdit caché dans un mot plus long n'est pas bloqué.
"""

import re
import unicodedata

from django.utils.html import strip_tags

# À COMPLÉTER : liste de mots générée par une IA, à valider par l'ENC.
MOTS_INTERDITS = [
    "abruti",
    "andouille",
    "andouille de merde",
    "andouillé",
    "bâtard",
    "batard",
    "baltringue",
    "blaireau",
    "bouffon",
    "branleur",
    "branleuse",
    "branquignol",
    "casse-couilles",
    "casse-bonbons",
    "connard",
    "connasse",
    "con",
    "conne",
    "connerie",
    "couillon",
    "couillonne",
    "crétin",
    "crétine",
    "débile",
    "dégénéré",
    "dégénérée",
    "enculé",
    "enculée",
    "enfoiré",
    "enfoirée",
    "emmerdeur",
    "emmerdeuse",
    "emmerder",
    "emmerdement",
    "fdp",
    "fils de pute",
    "foutre",
    "foutaise",
    "garce",
    "gland",
    "glandu",
    "gogol",
    "goujat",
    "grognasse",
    "idiot",
    "idiote",
    "imbécile",
    "lopette",
    "merde",
    "merdeux",
    "merdeuse",
    "merdique",
    "morue",
    "naze",
    "nègre",
    "ordure",
    "pétasse",
    "pignouf",
    "pingouin",
    "pouffiasse",
    "pute",
    "putain",
    "putain de merde",
    "raclure",
    "racaille",
    "salaud",
    "salaude",
    "salope",
    "schlag",
    "sous-merde",
    "suceur",
    "suceuse",
    "tapette",
    "tocard",
    "trouduc",
    "trou du cul",
    "tête de con",
    "va te faire foutre",
    "va te faire enculer",
    "victime",
    "zgeg",
    "zob",
    "bite",
    "couille",
    "cul",
    "chatte",
    "chier",
    "chiant",
    "chiante",
    "nique",
    "niquer",
    "nique ta mère",
    "nique ta race",
    "nique ta gueule",
    "tg",
    "ntm",
    "ta gueule",
    "ferme ta gueule",
    "ferme ton clapet",
    "casse-toi",
    "dégage",
]


def normaliser(texte):
    """Met le texte en minuscules et retire les accents : « Éte » devient « ete »."""
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return sans_accents.lower()


def mots_trouves(texte):
    """Les mots de la liste noire présents dans le texte (HTML accepté)."""
    texte = normaliser(strip_tags(texte))
    return [mot for mot in MOTS_INTERDITS if re.search(rf"\b{re.escape(normaliser(mot))}\b", texte)]
