"""
Le mentorat : un membre se déclare mentor (il accompagne d'autres membres), mentoré (il
cherche un mentor) ou les deux, sur des sujets. Le rôle reprend la colonne `mentoring_role` de
l'export Datalumni (`mentor`, `mentee` ou `mentor / mentee`, docs/migration/export-reel.md) ;
les sujets et le nombre maximum de mentorés ne sont pas dans l'export.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# À confirmer avec l'ENC : combien de mentorés un mentor peut-il suivre en même temps ?
NB_MAX_MENTORES = 10


class Sujet(models.Model):
    """Un sujet de mentorat (les « types de mentorat » de Datalumni), saisi dans le back-office."""

    nom = models.CharField("nom", max_length=100, unique=True)

    class Meta:
        verbose_name = "sujet de mentorat"
        verbose_name_plural = "sujets de mentorat"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class ProfilMentorat(models.Model):
    """
    Ce qu'un membre propose ou cherche. Il n'existe que si le membre participe au mentorat :
    un membre qui arrête supprime son profil.
    """

    class Role(models.TextChoices):
        MENTOR = "mentor", "Mentor"
        MENTORE = "mentore", "Mentoré"
        LES_DEUX = "mentor_et_mentore", "Mentor et mentoré"

    # Un seul profil par membre ; il disparaît avec le compte (suppression RGPD).
    membre = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_mentorat",
        verbose_name="membre",
    )
    role = models.CharField("rôle", max_length=20, choices=Role.choices)
    sujets = models.ManyToManyField(
        Sujet, blank=True, related_name="profils", verbose_name="sujets"
    )
    nb_max_mentores = models.PositiveSmallIntegerField(
        "nombre maximum de mentorés",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(NB_MAX_MENTORES)],
        help_text="Pour un mentor : combien de membres il peut accompagner en même temps.",
    )
    modifie_le = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        verbose_name = "profil de mentorat"
        verbose_name_plural = "profils de mentorat"
        ordering = ["membre__nom", "membre__prenom"]

    def __str__(self):
        return f"{self.membre} ({self.get_role_display()})"

    @property
    def accompagne(self):
        """Vrai pour un mentor, y compris un membre à la fois mentor et mentoré."""
        return self.role in (self.Role.MENTOR, self.Role.LES_DEUX)
