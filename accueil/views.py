from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from membres.droits import est_membre_valide
from membres.models import Membre
from membres.views import membres_de_l_annuaire
from referentiels.models import Diplome, Formation


@require_GET
def index(request):
    """Page d'accueil du site."""
    chiffres = {
        "promos": Formation.objects.values("promo").distinct().count(),
        "diplomes": Diplome.objects.count(),
        "membres": Membre.objects.filter(
            statut_inscription=Membre.StatutInscription.VALIDEE, is_active=True
        ).count(),
    }
    derniers_inscrits = []
    if est_membre_valide(request.user):
        derniers_inscrits = membres_de_l_annuaire().order_by("-cree_le")[:6]
    return render(
        request,
        "accueil/index.html",
        {"chiffres": chiffres, "derniers_inscrits": derniers_inscrits},
    )

    return render(request, "accueil/index.html", {"chiffres": chiffres})


@require_GET
def sante(request):
    """Répond « ok » : sert à vérifier que l'application tourne."""
    return HttpResponse("ok", content_type="text/plain")
