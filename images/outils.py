"""Outils communs pour les images envoyées par les membres (issue #92, fiche 0003)."""

from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

TAILLE_MAX = 5 * 1024 * 1024  # 5 Mo, en octets
LARGEUR_MAX = 1600  # en pixels


def verifier_taille(fichier):
    """Refuse une image de plus de 5 Mo (à utiliser comme validateur d'un ImageField)."""
    if fichier.size > TAILLE_MAX:
        raise ValidationError("L'image ne doit pas dépasser 5 Mo.")


def nettoyer_image(fichier):
    """Renvoie une copie de l'image sans métadonnées (EXIF), large de 1600 px au plus."""
    image = Image.open(fichier)
    format_origine = image.format
    image = ImageOps.exif_transpose(image)
    if image.width > LARGEUR_MAX:
        hauteur = round(image.height * LARGEUR_MAX / image.width)
        image = image.resize((LARGEUR_MAX, hauteur))
    tampon = BytesIO()
    image.save(tampon, format=format_origine)
    return ContentFile(tampon.getvalue(), name=fichier.name)
