from django.db import models


class MotInterdit(models.Model):
    mot = models.CharField("mot", max_length=100, unique=True)
    ajoute_le = models.DateTimeField("ajouté le", auto_now_add=True)

    class Meta:
        ordering = ["mot"]
        verbose_name = "mot interdit"
        verbose_name_plural = "mots interdits"

    def __str__(self):
        return self.mot

    def save(self, *args, **kwargs):
        self.mot = self.mot.strip().lower()
        super().save(*args, **kwargs)
