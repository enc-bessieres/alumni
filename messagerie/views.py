from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from membres.droits import reserve_aux_membres_valides
from membres.views import membres_de_l_annuaire

from .forms import NouveauMessage
from .models import Conversation, Message


def interlocuteurs(conversation, membre):
    return [p for p in conversation.participants.all() if p.pk != membre.pk]


@require_GET
@reserve_aux_membres_valides
def liste(request):
    """Les conversations du membre connecté, la plus récente en premier."""
    dernier = Message.objects.filter(conversation=OuterRef("pk")).order_by("-envoye_le", "-pk")
    conversations = request.user.conversations.annotate(
        dernier_message=Subquery(dernier.values("texte")[:1])
    ).prefetch_related("participants")
    lignes = [(c, interlocuteurs(c, request.user)) for c in conversations]
    return render(request, "messagerie/liste.html", {"lignes": lignes})


@require_http_methods(["GET", "POST"])
@reserve_aux_membres_valides
def conversation(request, pk):
    # Cherchée parmi les conversations du membre : celle des autres donne une 404, sans
    # dire qu'elle existe.
    conversation = get_object_or_404(request.user.conversations, pk=pk)
    formulaire = NouveauMessage(request.POST if request.method == "POST" else None)
    if formulaire.is_valid():
        Message.objects.create(
            conversation=conversation, auteur=request.user, texte=formulaire.cleaned_data["texte"]
        )
        conversation.save(update_fields=["modifiee_le"])
        # Après un envoi, on revient sur la page : un rechargement ne renvoie pas le message.
        return redirect(conversation)
    contexte = {
        "conversation": conversation,
        "interlocuteurs": interlocuteurs(conversation, request.user),
        "messages_de_la_conversation": conversation.messages.select_related("auteur"),
        "formulaire": formulaire,
    }
    return render(request, "messagerie/conversation.html", contexte)


@require_http_methods(["GET", "POST"])
@reserve_aux_membres_valides
def ecrire(request, pk):
    """Écrire à un membre de l'annuaire : la fiche, l'annuaire ou le mentorat y mèneront."""
    # Seulement un membre que l'annuaire montre (règle 5), et jamais soi-même.
    destinataire = get_object_or_404(membres_de_l_annuaire().exclude(pk=request.user.pk), pk=pk)
    existante = Conversation.entre(request.user, destinataire)
    if existante:
        return redirect(existante)

    formulaire = NouveauMessage(request.POST if request.method == "POST" else None)
    if formulaire.is_valid():
        nouvelle = Conversation.objects.create()
        nouvelle.participants.add(request.user, destinataire)
        Message.objects.create(
            conversation=nouvelle, auteur=request.user, texte=formulaire.cleaned_data["texte"]
        )
        return redirect(nouvelle)
    contexte = {"destinataire": destinataire, "formulaire": formulaire}
    return render(request, "messagerie/ecrire.html", contexte)
