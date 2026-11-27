"""
La messagerie privée : des conversations entre membres, comme dans Datalumni. Seuls les
participants d'une conversation la voient : elle n'apparaît pas dans le back-office.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse

LONGUEUR_MAX = 2000


class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="conversations", verbose_name="participants"
    )
    # Mise à jour à chaque message : la conversation la plus récente arrive en tête de liste.
    modifiee_le = models.DateTimeField("dernier message le", auto_now=True)

    class Meta:
        verbose_name = "conversation"
        verbose_name_plural = "conversations"
        ordering = ["-modifiee_le", "-pk"]

    def __str__(self):
        return f"Conversation n° {self.pk}"

    def get_absolute_url(self):
        return reverse("messagerie:conversation", args=[self.pk])

    @classmethod
    def entre(cls, membre, autre):
        """La conversation à deux entre ces membres, ou None s'ils ne se sont jamais écrit."""
        for conversation in cls.objects.filter(participants=membre).filter(participants=autre):
            if conversation.participants.count() == 2:
                return conversation
        return None


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    # Le compte supprimé (RGPD), ses messages restent lisibles par l'autre participant,
    # sans son nom.
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="messages_envoyes",
        verbose_name="auteur",
    )
    texte = models.TextField("message", max_length=LONGUEUR_MAX)
    envoye_le = models.DateTimeField("envoyé le", auto_now_add=True)

    class Meta:
        verbose_name = "message"
        verbose_name_plural = "messages"
        ordering = ["envoye_le", "pk"]

    def __str__(self):
        return self.texte[:50]
