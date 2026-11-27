"""
Page des validateurs (#89, décision docs/decisions/0005-annuaire-apres-validation.md).

Un nouvel inscrit entre sur le site dès que son adresse est vérifiée, mais l'annuaire et les
fiches restent fermés tant qu'un validateur n'a pas validé son inscription. Cette page liste
les inscriptions en attente ; « Valider » ou « Refuser » change le statut et prévient le
membre par e-mail.

Droit : la permission « valider_inscription » (groupes Validateur et Administrateur, dans
membres/droits.py). La vue ne décide pas elle-même qui a le droit (règle 3).
"""

import logging
import smtplib

from allauth.account.models import EmailAddress
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import Membre

journal = logging.getLogger(__name__)

# Au-delà, la page reste lisible : on montre les plus anciennes, et le nombre total.
NOMBRE_AFFICHE = 100

DECISIONS = {
    "valider": Membre.StatutInscription.VALIDEE,
    "refuser": Membre.StatutInscription.REFUSEE,
}


def reserve_aux_validateurs(vue):
    """Connecté (sinon page de connexion), avec la permission (sinon 403)."""
    return login_required(
        permission_required("membres.valider_inscription", raise_exception=True)(vue)
    )


@require_GET
@reserve_aux_validateurs
def inscriptions_en_attente(request):
    en_attente = Membre.objects.filter(
        statut_inscription=Membre.StatutInscription.EN_ATTENTE
    ).order_by("cree_le", "pk")  # la plus ancienne d'abord : personne n'attend trop longtemps
    contexte = {
        "membres": en_attente.annotate(
            adresse_verifiee=Exists(EmailAddress.objects.filter(user=OuterRef("pk"), verified=True))
        )[:NOMBRE_AFFICHE],
        "total": en_attente.count(),
    }
    return render(request, "membres/validation.html", contexte)


@require_POST
@reserve_aux_validateurs
def decider(request, pk):
    """Valide ou refuse une inscription en attente, puis prévient le membre par e-mail."""
    statut = DECISIONS.get(request.POST.get("decision"))
    if statut is None:
        messages.error(request, "Décision inconnue : rien n'a été changé.")
        return redirect("membres:validation")

    with transaction.atomic():
        # Seulement une inscription encore en attente : si un autre validateur vient de la
        # traiter, on ne revient pas sur sa décision, et le membre ne reçoit pas deux e-mails.
        membre = (
            Membre.objects.select_for_update()
            .filter(pk=pk, statut_inscription=Membre.StatutInscription.EN_ATTENTE)
            .first()
        )
        if membre is None:
            messages.info(request, "Cette inscription a déjà été traitée.")
            return redirect("membres:validation")
        membre.statut_inscription = statut
        membre.save(update_fields=["statut_inscription"])

    decision = "validée" if statut == Membre.StatutInscription.VALIDEE else "refusée"
    try:
        prevenir(request, membre)
    except (smtplib.SMTPException, OSError):
        # La décision est enregistrée ; seul l'e-mail n'est pas parti (serveur d'envoi en panne).
        # On le dit au validateur au lieu d'afficher une page d'erreur.
        journal.exception("E-mail de décision non envoyé au membre %s", membre.pk)
        messages.warning(
            request,
            f"Inscription de {membre} {decision}, mais l'e-mail n'a pas pu partir : "
            "prévenez le membre vous-même.",
        )
    else:
        messages.success(request, f"Inscription de {membre} {decision} : le membre est prévenu.")
    return redirect("membres:validation")


def prevenir(request, membre):
    """L'e-mail au membre : validée (avec le lien de l'annuaire) ou refusée."""
    gabarit = (
        "validee" if membre.statut_inscription == Membre.StatutInscription.VALIDEE else "refusee"
    )
    contexte = {
        "membre": membre,
        "lien_annuaire": request.build_absolute_uri(reverse("membres:annuaire")),
    }
    send_mail(
        subject=render_to_string(f"membres/emails/{gabarit}_sujet.txt", contexte).strip(),
        message=render_to_string(f"membres/emails/{gabarit}.txt", contexte),
        from_email=None,  # DEFAULT_FROM_EMAIL
        recipient_list=[membre.email],
    )
