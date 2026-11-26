"""
Le formulaire d'inscription. django-allauth s'occupe de l'e-mail et du mot de passe
(adresse unique, vérification par e-mail, règles de mot de passe, limite de tentatives) ;
ce formulaire ajoute ce qu'il faut savoir du nouveau membre.

Décision docs/decisions/0005 : un nouvel inscrit entre sur le site dès que son adresse est
vérifiée, mais son inscription reste « en attente » : l'annuaire et les fiches ne s'ouvrent
qu'après la validation d'un validateur (reserve_aux_membres_valides, dans droits.py).
"""

from django import forms
from django.contrib import messages

from .models import Membre


class InscriptionForm(forms.Form):
    civilite = forms.ChoiceField(
        label="Civilité", required=False, choices=[("", "—")] + Membre.Civilite.choices
    )
    prenom = forms.CharField(label="Prénom", max_length=150)
    nom = forms.CharField(label="Nom", max_length=150)
    nom_de_naissance = forms.CharField(
        label="Nom de naissance",
        max_length=150,
        required=False,
        help_text="S'il est différent : vos camarades de promo le connaissent peut-être.",
    )
    categorie = forms.ChoiceField(
        label="Vous êtes",
        choices=[("", "— Choisissez —")] + Membre.Categorie.choices,
    )
    cgu = forms.BooleanField(
        label="J'accepte les conditions générales d'utilisation",
        error_messages={"required": "Vous devez accepter les CGU pour vous inscrire."},
    )
    # Piège à robots : ce champ est caché aux personnes (attribut hidden dans le gabarit).
    # Un robot qui remplit tous les champs se trahit ; une personne le laisse vide.
    site_web = forms.CharField(label="Ne pas remplir ce champ", required=False)

    def clean_site_web(self):
        if self.cleaned_data["site_web"]:
            # Message volontairement vague : on n'explique pas au robot ce qui l'a trahi.
            raise forms.ValidationError("L'inscription n'a pas pu aboutir. Réessayez.")
        return ""

    def signup(self, request, user):
        """Appelé par allauth une fois le compte créé : on complète la fiche du membre."""
        for champ in ("civilite", "prenom", "nom", "nom_de_naissance", "categorie"):
            setattr(user, champ, self.cleaned_data[champ])
        # Le statut est décidé ici, jamais par ce que le visiteur envoie : un champ
        # statut_inscription, is_staff ou groupes ajouté à la main est ignoré.
        user.statut_inscription = Membre.StatutInscription.EN_ATTENTE
        user.save()
        messages.info(
            request,
            "Bienvenue ! Vérifiez votre adresse e-mail pour entrer sur le site. L'annuaire "
            "s'ouvrira dès que l'équipe de l'ENC Bessières aura validé votre inscription.",
        )
