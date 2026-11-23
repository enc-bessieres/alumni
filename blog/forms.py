from django import forms

from moderation.filtres import mots_trouves

from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["titre", "resume", "contenu"]

    def clean(self):
        donnees = super().clean()
        texte = " ".join(
            [donnees.get("titre", ""), donnees.get("resume", ""), donnees.get("contenu", "")]
        )
        if mots_trouves(texte):
            raise forms.ValidationError(
                "Votre article contient un mot interdit. Merci de le reformuler."
            )
        return donnees
