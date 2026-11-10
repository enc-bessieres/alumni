"""
Crée les sites, niveaux et diplômes de `donnees.py` qui manquent encore.

On reçoit les classes de modèles en paramètre : la migration 0002 passe les modèles
« historiques » (ceux de l'époque de la migration, comme Django le demande), et les tests
passent les vrais. On peut relancer la fonction : `get_or_create` ne crée que ce qui manque.
"""

from .donnees import DIPLOMES, NIVEAUX, SITES


def creer_referentiels(Site, Niveau, Diplome):  # des classes de modèles, d'où la majuscule
    for nom in SITES:
        Site.objects.get_or_create(nom=nom)
    for nom_niveau in NIVEAUX:
        niveau, _ = Niveau.objects.get_or_create(nom=nom_niveau)
        for nom in DIPLOMES[nom_niveau]:
            Diplome.objects.get_or_create(nom=nom, defaults={"niveau": niveau})
