from django import forms

from .models import LONGUEUR_MAX


class NouveauMessage(forms.Form):
    texte = forms.CharField(
        label="Votre message",
        max_length=LONGUEUR_MAX,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
