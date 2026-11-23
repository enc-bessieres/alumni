from django import forms

from .models import Article
from .moderation import mots_trouves


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["titre", "resume", "contenu"]

    def clean(self):
        donnees = super().clean()
        texte = f"{donnees.get('titre', '')} {donnees.get('contenu', '')}"
        if mots_trouves(texte):
            raise forms.ValidationError(
                "Votre article contient un mot interdit. Merci de le reformuler."
            )
        return donnees
