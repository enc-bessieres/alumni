from django import forms

from referentiels.models import Diplome, Formation, Site

from .models import Experience, Membre


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


class ParametresForm(forms.ModelForm):
    """
    Les réglages que le membre change lui-même. Seuls les champs listés ici peuvent être
    modifiés : un champ ajouté à la main dans la requête (is_staff, groupes…) est ignoré.
    """

    class Meta:
        model = Membre
        fields = ["visible_dans_annuaire", "email_visible", "linkedin"]
        labels = {
            "visible_dans_annuaire": "Apparaître dans l'annuaire",
            "email_visible": "Montrer mon adresse e-mail sur ma fiche",
            "linkedin": "Mon profil LinkedIn",
        }
        help_texts = {
            "visible_dans_annuaire": (
                "Les membres validés voient votre nom, votre catégorie et vos diplômes, jamais "
                "votre adresse e-mail. Décochez pour ne plus apparaître dans l'annuaire."
            ),
            "email_visible": "Seuls les membres validés voient votre fiche.",
            "linkedin": "Facultatif. Par exemple https://www.linkedin.com/in/prenom-nom/",
        }
        # Le lecteur d'écran lit l'explication avec chaque champ (accessibilité).
        widgets = {
            "visible_dans_annuaire": forms.CheckboxInput(
                attrs={"aria-describedby": "id_visible_dans_annuaire_aide"}
            ),
            "email_visible": forms.CheckboxInput(
                attrs={"aria-describedby": "id_email_visible_aide"}
            ),
            "linkedin": forms.URLInput(attrs={"aria-describedby": "id_linkedin_aide"}),
        }


# Le parcours : toutes les expériences du membre dans un seul formulaire, plus une ligne vide pour
# en ajouter une. Le jeu de formulaires est lié au membre connecté : il ne peut ni voir ni
# modifier les expériences d'un autre, même en trafiquant les identifiants envoyés.
ParcoursFormSet = forms.inlineformset_factory(
    Membre,
    Experience,
    fields=["intitule", "organisation", "secteur", "lieu", "debut", "fin"],
    extra=1,
    can_delete=True,
    can_delete_extra=False,  # pas de case « Supprimer » sur la ligne vide
    max_num=20,
    validate_max=True,
)
