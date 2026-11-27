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
        trouves = mots_trouves(texte)
        if trouves:
            raise forms.ValidationError(
                "Votre article contient un mot interdit : %(mots)s. Merci de le reformuler.",
                params={"mots": ", ".join(trouves)},
            )
        return donnees
