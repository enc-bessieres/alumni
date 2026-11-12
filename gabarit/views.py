from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def bientot(request, titre):
    """Page provisoire derrière une entrée du menu, en attendant la vraie page du domaine."""
    return render(request, "gabarit/bientot.html", {"titre": titre})
