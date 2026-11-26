from django.core.exceptions import ValidationError
from django.db import models

from texte_riche.champs import ChampTexteRiche


class Evenement(models.Model):
    """Un événement proposé ou publié sur le site Alumni."""

    titre = models.CharField("titre", max_length=200)
    description = ChampTexteRiche("description", blank=True)
    date_debut = models.DateTimeField("date de début")
    date_fin = models.DateTimeField("date de fin", null=True, blank=True)
    lieu = models.CharField("lieu", max_length=200, blank=True)
    publie = models.BooleanField("publié", default=False)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)

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
