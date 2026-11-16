from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.internal.stagekit import clear_login
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

    def is_open_for_signup(self, request):
        # L'inscription en étapes arrive avec sa propre PR : d'ici là, elle reste fermée.
        return False

    def pre_login(self, request, user, **kwargs):
        """
        Appelé par allauth juste avant d'ouvrir la session, une fois le mot de passe vérifié.
        Seul un membre dont l'inscription est validée peut se connecter ; les autres
        restent sur la page de connexion, avec un message qui dit pourquoi.
        """
        if user.statut_inscription != Membre.StatutInscription.VALIDEE:
            clear_login(request)  # oublie la connexion commencée, comme le fait allauth
            messages.error(request, MESSAGES_REFUS[user.statut_inscription])
            return redirect("account_login")
        return super().pre_login(request, user, **kwargs)
