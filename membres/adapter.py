from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect

from .models import Membre

# Ce qu'on dit à un membre dont l'inscription n'est pas (ou plus) validée.
MESSAGES_REFUS = {
    Membre.StatutInscription.EN_ATTENTE: (
        "Votre inscription est en attente de validation. "
        "Vous pourrez vous connecter dès qu'elle aura été validée."
    ),
    Membre.StatutInscription.REFUSEE: (
        "Votre inscription a été refusée. "
        "Pour en savoir plus, contactez l'équipe de l'ENC Bessières."
    ),
}


class AdaptateurCompte(DefaultAccountAdapter):
    """Nos réglages de django-allauth qui ne tiennent pas dans settings.py."""

    def login(self, request, user):
        """
        Appelé par allauth au moment précis d'ouvrir la session, quel que soit le chemin :
        mot de passe, ou clic sur le lien de vérification de l'adresse e-mail
        (ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION). Seul un membre dont l'inscription est validée
        peut se connecter ; les autres reviennent à la page de connexion, avec un message.

        Le contrôle est ici et pas dans pre_login : la connexion par le lien de vérification
        reprend la connexion commencée à l'inscription et ne repasse pas par pre_login.
        """
        if user.statut_inscription != Membre.StatutInscription.VALIDEE:
            messages.error(request, MESSAGES_REFUS[user.statut_inscription])
            raise ImmediateHttpResponse(redirect("account_login"))
        super().login(request, user)
