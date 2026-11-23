"""
Recherche des mots de la liste noire (décision de #43), modifiable dans le back-office.

La recherche ignore les majuscules et les accents, et ne cherche que des mots entiers :
un mot interdit caché dans un mot plus long n'est pas bloqué.
"""

import re
import unicodedata

from django.utils.html import strip_tags

from .models import MotInterdit


def normaliser(texte):
    """Met le texte en minuscules et retire les accents : « Éte » devient « ete »."""
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return sans_accents.lower()


def mots_trouves(texte):
    """Les mots de la liste noire présents dans le texte (HTML accepté)."""
    texte = normaliser(strip_tags(texte))
    return [
        mot
        for mot in MotInterdit.objects.values_list("mot", flat=True)
        if re.search(rf"\b{re.escape(normaliser(mot))}\b", texte)
    ]
