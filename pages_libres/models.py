from django.db import models


class Page(models.Model):
    """Une page éditable dans le back-office : À propos, mentions légales, CGU…"""

    titre = models.CharField("titre", max_length=200)
    slug = models.SlugField("adresse", unique=True, help_text="Exemple : mentions-legales")
    contenu = models.TextField("contenu")
    publiee = models.BooleanField("publiée", default=False)
    modifiee_le = models.DateTimeField("dernière modification", auto_now=True)

    class Meta:
        ordering = ["titre"]
        verbose_name = "page libre"
        verbose_name_plural = "pages libres"

    def __str__(self):
        return self.titre
