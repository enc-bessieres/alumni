"""
Les référentiels de l'école : sites, niveaux, diplômes (vocabulaire d'AGENTS.md).
Les données elles-mêmes sont dans `donnees.py` et sont créées par la migration 0002.
"""

from django.db import models


class Referentiel(models.Model):
    """Ce qui est commun aux trois référentiels. `abstract` : pas de table pour cette classe."""

    nom = models.CharField("nom", max_length=100, unique=True)
    # Identifiant (UUID) du groupe chez Datalumni : l'import retrouve l'élément par ce champ,
    # donc on peut le rejouer sans doublon. Vide pour ce qui est créé sur le nouveau site.
    # `editable=False` : aucun formulaire ne peut le modifier, seul l'import l'écrit.
    legacy_id = models.UUIDField(
        "identifiant Datalumni", unique=True, null=True, blank=True, editable=False
    )

    class Meta:
        abstract = True
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Site(Referentiel):
    """Établissement : ENC Bessières, ENC Bessières Apprentissage."""

    class Meta(Referentiel.Meta):
        verbose_name = "site"
        verbose_name_plural = "sites"


class Niveau(Referentiel):
    """Niveau de formation : BTS, Prépa."""

    class Meta(Referentiel.Meta):
        verbose_name = "niveau"
        verbose_name_plural = "niveaux"


class Diplome(Referentiel):
    """Une des 20 formations (BTS SIO, DCG…), rattachée à un niveau.

    Le site n'est pas porté par le diplôme mais par le parcours d'un membre
    (membre + diplôme + site + promo), qui arrive avec le modèle Membre.
    """

    # PROTECT : on ne peut pas supprimer un niveau tant que des diplômes y sont rattachés.
    niveau = models.ForeignKey(
        Niveau, on_delete=models.PROTECT, related_name="diplomes", verbose_name="niveau"
    )

    class Meta(Referentiel.Meta):
        verbose_name = "diplôme"
        verbose_name_plural = "diplômes"
