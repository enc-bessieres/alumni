from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from images.outils import verifier_taille
from texte_riche.champs import ChampTexteRiche


class Article(models.Model):
    titre = models.CharField("titre", max_length=200)
    slug = models.SlugField("adresse", unique=True)
    resume = models.CharField("résumé", max_length=200, blank=True)
    contenu = ChampTexteRiche("contenu")
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name="auteur",
    )
    image = models.ImageField(
        "image", upload_to="articles/", blank=True, validators=[verifier_taille]
    )
    texte_alternatif = models.CharField(
        "texte alternatif",
        max_length=200,
        blank=True,
        help_text="Décrivez l'image pour les personnes qui ne la voient pas.",
    )

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_ATTENTE = "en_attente", "En attente de validation"
        PUBLIE = "publie", "Publié"
        REFUSE = "refuse", "Refusé"

    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.BROUILLON
    )
    publie_le = models.DateTimeField("publié le", null=True, blank=True)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)
    legacy_id = models.UUIDField(
        "identifiant Datalumni", unique=True, null=True, blank=True, editable=False
    )

    class Meta:
        ordering = ["-publie_le"]
        verbose_name = "article"
        verbose_name_plural = "articles"

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if self.statut == self.Statut.PUBLIE and self.publie_le is None:
            self.publie_le = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", args=[self.slug])
