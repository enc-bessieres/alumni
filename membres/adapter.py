from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect

from .models import Membre

MESSAGE_REFUSEE = (
    "Votre inscription a été refusée. Pour en savoir plus, contactez l'équipe de l'ENC Bessières."
)
MESSAGE_EN_ATTENTE = (
    "Votre inscription est en attente de validation : l'annuaire et les fiches des membres "
    "s'ouvriront dès que l'équipe l'aura validée."
)


class AdaptateurCompte(DefaultAccountAdapter):
    """Nos réglages de django-allauth qui ne tiennent pas dans settings.py."""

    def login(self, request, user):
        """
        Appelé par allauth au moment précis d'ouvrir la session, quel que soit le chemin :
        mot de passe, ou clic sur le lien de vérification de l'adresse e-mail
        (ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION).
        - inscription refusée : pas de connexion, retour à la page de connexion avec un message ;
        - inscription en attente : connexion, avec un message ; l'annuaire et les fiches restent
          fermés tant qu'un validateur n'a pas validé l'inscription (décision 0005).

        Le contrôle est ici et pas dans pre_login : la connexion par le lien de vérification
        reprend la connexion commencée à l'inscription et ne repasse pas par pre_login.
        """
        if user.statut_inscription == Membre.StatutInscription.REFUSEE:
            messages.error(request, MESSAGE_REFUSEE)
            raise ImmediateHttpResponse(redirect("account_login"))
        super().login(request, user)
        if user.statut_inscription == Membre.StatutInscription.EN_ATTENTE:
            messages.info(request, MESSAGE_EN_ATTENTE)
