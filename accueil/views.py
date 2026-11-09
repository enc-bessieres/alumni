from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def index(request):
    """Page d'accueil du site."""
    return render(request, "accueil/index.html")


@require_GET
def sante(request):
    """Répond « ok » : sert à vérifier que l'application tourne."""
    return HttpResponse("ok", content_type="text/plain")
