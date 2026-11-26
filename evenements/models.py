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
