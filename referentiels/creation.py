"""
Crée les sites, niveaux et diplômes de `donnees.py` qui manquent encore.

Sert au générateur de fausses données et aux tests. La migration 0002 ne s'en sert PAS :
elle a ses propres listes, figées (voir son en-tête).
On reçoit les classes de modèles en paramètre, et on peut relancer la fonction :
`get_or_create` ne crée que ce qui manque.
"""

from .donnees import DIPLOMES, NIVEAUX, SITES


def creer_referentiels(Site, Niveau, Diplome):  # des classes de modèles, d'où la majuscule
    for nom in SITES:
        Site.objects.get_or_create(nom=nom)
    for nom_niveau in NIVEAUX:
        niveau, _ = Niveau.objects.get_or_create(nom=nom_niveau)
        for nom in DIPLOMES[nom_niveau]:
            Diplome.objects.get_or_create(nom=nom, defaults={"niveau": niveau})
