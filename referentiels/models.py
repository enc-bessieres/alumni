"""
Les référentiels de l'école : sites, niveaux, diplômes (vocabulaire d'AGENTS.md), et le parcours
de chaque membre (Formation). Les référentiels sont créés par la migration 0002.

Les référentiels d'administration (#39) servent aux autres domaines : types de contrat pour les
offres (Vera), secteurs et tags pour les profils et l'annuaire (Alex). Leurs listes de départ
sont créées par la migration 0005, et se modifient ensuite dans le back-office.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
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
    (membre + diplôme + site + promo) : voir le modèle Formation.
    """

    # PROTECT : on ne peut pas supprimer un niveau tant que des diplômes y sont rattachés.
    niveau = models.ForeignKey(
        Niveau, on_delete=models.PROTECT, related_name="diplomes", verbose_name="niveau"
    )

    class Meta(Referentiel.Meta):
        verbose_name = "diplôme"
        verbose_name_plural = "diplômes"


class TypeDeContrat(Referentiel):
    """Le contrat d'une offre d'emploi ou de stage : CDI, CDD, Stage, Alternance…"""

    class Meta(Referentiel.Meta):
        verbose_name = "type de contrat"
        verbose_name_plural = "types de contrat"


class Secteur(Referentiel):
    """Un secteur d'activité : celui d'une expérience, d'une offre, d'un filtre de l'annuaire."""

    class Meta(Referentiel.Meta):
        verbose_name = "secteur"
        verbose_name_plural = "secteurs"


class Tag(Referentiel):
    """Un mot-clé de profil, géré dans le back-office (vide au départ, comme on ne sait pas
    encore lesquels Datalumni utilise)."""

    class Meta(Referentiel.Meta):
        verbose_name = "tag"
        verbose_name_plural = "tags"


class Formation(models.Model):
    """Le parcours d'un membre : un diplôme, sur un site, avec sa promo (année de sortie).

    Un membre peut avoir plusieurs diplômes, donc plusieurs formations, et donc plusieurs promos.
    """

    # CASCADE : si un membre supprime son compte, son parcours part avec lui (RGPD).
    membre = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="formations",
        verbose_name="membre",
    )
    # PROTECT : on ne peut pas supprimer un diplôme ou un site que des membres ont suivi.
    diplome = models.ForeignKey(
        Diplome, on_delete=models.PROTECT, related_name="formations", verbose_name="diplôme"
    )
    site = models.ForeignKey(
        Site, on_delete=models.PROTECT, related_name="formations", verbose_name="site"
    )
    promo = models.PositiveSmallIntegerField(
        "promo",
        help_text="Année de sortie, par exemple 2024.",
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
    )
    # Même rôle que pour les référentiels : import Datalumni rejouable sans doublon.
    legacy_id = models.UUIDField(
        "identifiant Datalumni", unique=True, null=True, blank=True, editable=False
    )

    class Meta:
        verbose_name = "formation"
        verbose_name_plural = "formations"
        ordering = ["-promo", "diplome__nom"]
        constraints = [
            # Un même diplôme ne compte qu'une fois dans le parcours d'un membre.
            models.UniqueConstraint(
                fields=["membre", "diplome"], name="formation_un_diplome_par_membre"
            ),
        ]

    def __str__(self):
        return f"{self.diplome} {self.promo} ({self.site})"
