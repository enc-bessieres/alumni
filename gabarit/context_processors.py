"""Variables ajoutées à toutes les pages, pour que le gabarit les affiche."""

from django.urls import reverse

from .menu import MENU, NB_ENTREES_MOBILE


def _est_actif(url, chemin):
    """L'accueil n'est actif que sur « / » ; une autre entrée l'est aussi sur ses sous-pages."""
    if url == "/":
        return chemin == "/"
    return chemin.startswith(url)


def menu(request):
    entrees = []
    for entree in MENU:
        url = reverse(entree.nom_url)
        entrees.append(
            {"libelle": entree.libelle, "url": url, "actif": _est_actif(url, request.path)}
        )
    return {
        "menu": entrees,
        "menu_mobile": entrees[:NB_ENTREES_MOBILE],
        "menu_plus": entrees[NB_ENTREES_MOBILE:],
    }
