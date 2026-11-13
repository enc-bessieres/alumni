"""Variables ajoutées à toutes les pages, pour que le gabarit les affiche."""

from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import NoReverseMatch, reverse

from .menu import MENU, NB_ENTREES_MOBILE, PIED_DE_PAGE


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


def compte(request):
    """Ce que la zone membre affiche.

    La connexion et la déconnexion viennent de django-allauth, installé par Alex (issue #9) :
    tant que sa déconnexion n'existe pas, le bouton reste masqué.
    """
    try:
        url_deconnexion = reverse("account_logout")
    except NoReverseMatch:
        url_deconnexion = None

    # Les initiales passent par les méthodes standard d'un compte Django : elles marchent avec
    # le modèle Membre d'Alex comme avec le compte par défaut.
    membre = getattr(request, "user", None)
    initiales = ""
    if membre is not None and membre.is_authenticated:
        mots = membre.get_full_name().split() or [membre.get_username()]
        initiales = "".join(mot[0] for mot in mots[:2]).upper()

    return {
        "url_connexion": resolve_url(settings.LOGIN_URL),
        "url_deconnexion": url_deconnexion,
        "initiales": initiales,
    }


def pied_de_page(request):
    """Liens du pied de page vers les pages libres de Marie-Dominique (issue #12).

    Tant que son application « pages_libres » n'est pas installée, la liste reste vide
    et le pied de page garde son « À COMPLÉTER ».
    """
    try:
        liens = [
            {"libelle": lien.libelle, "url": reverse("pages_libres:detail", args=[lien.slug])}
            for lien in PIED_DE_PAGE
        ]
    except NoReverseMatch:
        liens = []
    return {"liens_du_pied": liens}
