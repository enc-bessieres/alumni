from django import forms

from .models import ProfilMentorat

# Le choix vide permet de ne pas participer, ou d'arrêter : le profil est alors supprimé.
CHOIX_DU_ROLE = [
    ("", "Je ne participe pas au mentorat"),
    (ProfilMentorat.Role.MENTOR, "Mentor : j'accompagne d'autres membres"),
    (ProfilMentorat.Role.MENTORE, "Mentoré : je cherche un mentor"),
    (ProfilMentorat.Role.LES_DEUX, "Les deux : j'accompagne et je cherche un mentor"),
]

# Les rôles qui accompagnent d'autres membres, et ont donc un nombre maximum de mentorés.
ROLES_QUI_ACCOMPAGNENT = (ProfilMentorat.Role.MENTOR, ProfilMentorat.Role.LES_DEUX)


class PreferencesMentorat(forms.ModelForm):
    # Hors des champs du modèle : « ne pas participer » n'est pas un rôle qu'on enregistre.
    role = forms.ChoiceField(
        label="Je participe au mentorat",
        choices=CHOIX_DU_ROLE,
        required=False,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = ProfilMentorat
        # Pas de champ « membre » : c'est toujours le membre connecté, fixé par la vue.
        fields = ["sujets", "nb_max_mentores"]
        widgets = {"sujets": forms.CheckboxSelectMultiple}

    field_order = ["role", "sujets", "nb_max_mentores"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["role"].initial = self.instance.role
        # Obligatoire pour qui accompagne seulement : vérifié dans clean().
        self.fields["nb_max_mentores"].required = False

    def clean(self):
        donnees = super().clean()
        if donnees.get("role") in ROLES_QUI_ACCOMPAGNENT:
            if donnees.get("nb_max_mentores") is None and "nb_max_mentores" not in self.errors:
                self.add_error(
                    "nb_max_mentores", "Indiquez combien de membres vous pouvez accompagner."
                )
        else:
            # Seul un mentor a un nombre maximum de mentorés : valeur par défaut pour les autres.
            donnees["nb_max_mentores"] = 1
        return donnees
