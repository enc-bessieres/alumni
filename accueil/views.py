from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from membres.models import Membre
from referentiels.models import Diplome, Formation


@require_GET
def index(request):
    """Page d'accueil du site."""
    chiffres = {
        "membres": Membre.objects.filter(
            statut_inscription=Membre.StatutInscription.VALIDEE
        ).count(),
        "promos": Formation.objects.values("promo").distinct().count(),
        "diplomes": Diplome.objects.count(),
    }
    return render(request, "accueil/index.html", {"chiffres": chiffres})


@require_GET
def sante(request):
    """Répond « ok » : sert à vérifier que l'application tourne."""
    return HttpResponse("ok", content_type="text/plain")
