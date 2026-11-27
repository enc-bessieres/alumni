from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from texte_riche.champs import ChampTexteRiche


class Evenement(models.Model):
    """Un événement proposé ou publié sur le site Alumni."""

    titre = models.CharField("titre", max_length=200)
    slug = models.SlugField("slug", max_length=200, unique=True)
    description = ChampTexteRiche("description", blank=True)
    date_debut = models.DateTimeField("date de début")
    date_fin = models.DateTimeField("date de fin", null=True, blank=True)
    lieu = models.CharField("lieu", max_length=200, blank=True)
    places = models.PositiveIntegerField(
        "places",
        null=True,
        blank=True,
        help_text="Laisser vide s'il n'y a pas de limite de places.",
    )
    organisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evenements_organises",
        verbose_name="organisateur",
    )
    publie = models.BooleanField("publié", default=False)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)
    legacy_id = models.UUIDField(
        "identifiant Datalumni", unique=True, null=True, blank=True, editable=False
    )

    class Meta:
        ordering = ["-date_debut"]
        verbose_name = "événement"
        verbose_name_plural = "événements"

    def __str__(self):
        return self.titre

    def clean(self):
        super().clean()
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError(
                {"date_fin": "La date de fin ne peut pas précéder la date de début."}
            )
