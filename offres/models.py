from django.conf import settings
from django.db import models

from texte_riche.champs import ChampTexteRiche


class Offre(models.Model):
    """Une offre d'emploi ou de stage déposée par un membre et validée par l'administration."""

    class Experience(models.TextChoices):
        DEBUTANT = "debutant", "Débutant accepté"
        UN_A_TROIS = "1-3", "1 à 3 ans"
        PLUS_DE_TROIS = "3+", "Plus de 3 ans"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        PUBLIEE = "publiee", "Publiée"
        REFUSEE = "refusee", "Refusée"
        POURVUE = "pourvue", "Pourvue"

    titre = models.CharField("titre", max_length=200)
    organisation = models.CharField("organisation", max_length=200)
    type_de_contrat = models.ForeignKey(
        "referentiels.TypeDeContrat",
        verbose_name="type de contrat",
        on_delete=models.PROTECT,
    )
    secteur = models.ForeignKey(
        "referentiels.Secteur",
        verbose_name="secteur d'activité",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    lieu = models.CharField("lieu", max_length=200)
    description = ChampTexteRiche("description")
    remuneration = models.CharField(
        "rémunération", max_length=100, blank=True, help_text="Exemple : < 15k €"
    )
    experience = models.CharField(
        "expérience demandée",
        max_length=10,
        choices=Experience.choices,
        default=Experience.DEBUTANT,
    )
    date_limite = models.DateField("date limite", null=True, blank=True)
    email_contact = models.EmailField("e-mail de contact")
    lien_candidature = models.URLField("lien de candidature", blank=True)
    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="auteur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    legacy_id = models.UUIDField(
        "identifiant Datalumni", unique=True, null=True, blank=True, editable=False
    )
    creee_le = models.DateTimeField("date de création", auto_now_add=True)

    class Meta:
        ordering = ["-creee_le"]
        verbose_name = "offre"
        verbose_name_plural = "offres"
        permissions = [("valider_offre", "Peut valider ou refuser une offre")]

    def __str__(self):
        return f"{self.titre} ({self.organisation})"