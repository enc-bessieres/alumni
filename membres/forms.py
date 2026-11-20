from django import forms

from referentiels.models import Diplome, Formation, Site

from .models import Membre


class FiltresAnnuaire(forms.Form):
    """
    La recherche et les filtres de l'annuaire. Ils arrivent dans l'adresse (?q=…&promo=…) :
    une recherche se partage par un simple lien. Tous les champs sont facultatifs.
    """

    q = forms.CharField(label="Nom ou prénom", required=False, max_length=100)
    categorie = forms.ChoiceField(
        label="Catégorie",
        required=False,
        choices=[("", "Toutes")] + Membre.Categorie.choices,
    )
    site = forms.ModelChoiceField(
        label="Site", required=False, queryset=Site.objects.all(), empty_label="Tous"
    )
    diplome = forms.ModelChoiceField(
        label="Diplôme", required=False, queryset=Diplome.objects.all(), empty_label="Tous"
    )
    promo = forms.TypedChoiceField(label="Promo", required=False, coerce=int, empty_value=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Seulement les promos qui existent, de la plus récente à la plus ancienne.
        promos = Formation.objects.order_by("-promo").values_list("promo", flat=True).distinct()
        self.fields["promo"].choices = [("", "Toutes")] + [(p, p) for p in promos]
