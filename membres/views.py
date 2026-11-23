from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_GET, require_http_methods

from referentiels.models import Formation

from .droits import reserve_aux_membres_valides
from .forms import FiltresAnnuaire, ParametresForm, ParcoursFormSet
from .models import Membre

MEMBRES_PAR_PAGE = 25


def membres_de_l_annuaire():
    """Les membres qu'on a le droit de montrer : validés, actifs, et qui l'ont choisi (règle 5)."""
    membres = Membre.objects.filter(
        visible_dans_annuaire=True,
        is_active=True,
        statut_inscription=Membre.StatutInscription.VALIDEE,
    )
    # pk en dernier : deux homonymes gardent le même ordre d'une page à l'autre.
    return membres.order_by("nom", "prenom", "pk")


def formations_completes():
    """Les formations avec leur diplôme et leur site, chargés en une requête (pas de N+1)."""
    return Prefetch("formations", queryset=Formation.objects.select_related("diplome", "site"))


def filtrer(membres, filtres):
    """Applique la recherche et les filtres (des valeurs déjà validées par le formulaire)."""
    # Chaque mot doit se trouver dans le prénom ou le nom, sans tenir compte des accents ni des
    # majuscules : « lea martin » trouve « Léa Martin ». L'ORM passe les mots en paramètres de
    # la requête, jamais collés dans le SQL (règle 4).
    for mot in filtres.get("q", "").split():
        membres = membres.filter(
            Q(prenom__unaccent__icontains=mot) | Q(nom__unaccent__icontains=mot)
        )
    if filtres.get("categorie"):
        membres = membres.filter(categorie=filtres["categorie"])

    # Diplôme, site et promo doivent être ceux d'UNE MÊME formation : « BTS SIO, promo 2020 »
    # ne doit pas trouver un membre qui a un BTS SIO en 2012 et un DCG en 2020.
    conditions = {
        champ: filtres[champ] for champ in ("diplome", "site", "promo") if filtres.get(champ)
    }
    if conditions:
        formations = Formation.objects.filter(membre=OuterRef("pk"), **conditions)
        membres = membres.filter(Exists(formations))  # Exists : chaque membre une seule fois
    return membres


@require_GET
@reserve_aux_membres_valides
def annuaire(request):
    formulaire = FiltresAnnuaire(request.GET)
    # Une valeur invalide (promo=abc…) est ignorée : on garde seulement les filtres valides.
    formulaire.is_valid()
    membres = filtrer(membres_de_l_annuaire(), formulaire.cleaned_data)
    # Les formations des 25 membres de la page en une requête, au lieu d'une par membre.
    membres = membres.prefetch_related(formations_completes())
    page = Paginator(membres, MEMBRES_PAR_PAGE).get_page(request.GET.get("page"))

    # Les liens « Page suivante » gardent la recherche et les filtres : ?q=…&promo=…&page=
    parametres = request.GET.copy()
    parametres.pop("page", None)
    lien_page = f"?{parametres.urlencode()}&page=" if parametres else "?page="
    contexte = {"formulaire": formulaire, "page": page, "lien_page": lien_page}

    # HTMX ne redemande que la liste ; un retour arrière du navigateur redemande la page entière.
    partiel = (
        "HX-Request" in request.headers and "HX-History-Restore-Request" not in request.headers
    )
    gabarit = "membres/_resultats.html" if partiel else "membres/annuaire.html"
    reponse = render(request, gabarit, contexte)
    # La même adresse renvoie la page entière ou la liste seule : le cache doit les distinguer.
    patch_vary_headers(reponse, ["HX-Request"])
    return reponse


@require_GET
@reserve_aux_membres_valides
def fiche(request, pk):
    """
    La fiche d'un membre de l'annuaire. Un membre masqué, en attente, refusé ou inactif
    donne une 404, comme s'il n'existait pas. Seule exception : chacun voit sa propre fiche,
    même masquée, pour savoir ce que les autres verront.
    """
    if pk == request.user.pk:
        membres = Membre.objects.all()
    else:
        membres = membres_de_l_annuaire()
    membre = get_object_or_404(
        membres.prefetch_related(formations_completes(), "experiences"), pk=pk
    )
    return render(request, "membres/fiche.html", {"membre": membre})


@require_http_methods(["GET", "POST"])
@reserve_aux_membres_valides
def parametres(request):
    """
    Le membre règle ses propres paramètres. Pas d'identifiant dans l'adresse : on modifie
    toujours le compte connecté (request.user), jamais celui d'un autre.
    """
    # Une case décochée n'est pas envoyée : le formulaire doit être lié dès qu'il y a un POST.
    donnees = request.POST if request.method == "POST" else None
    formulaire = ParametresForm(donnees, instance=request.user)
    if formulaire.is_bound and formulaire.is_valid():
        formulaire.save()
        messages.success(request, "Vos paramètres sont enregistrés.")
        # Redirection après l'envoi : recharger la page ne renvoie pas le formulaire.
        return redirect("membres:parametres")
    return render(request, "membres/parametres.html", {"formulaire": formulaire})


@require_http_methods(["GET", "POST"])
@reserve_aux_membres_valides
def profil(request):
    """Le membre complète son parcours. Comme Paramètres : toujours son propre compte."""
    donnees = request.POST if request.method == "POST" else None
    parcours = ParcoursFormSet(donnees, instance=request.user, prefix="parcours")
    if parcours.is_bound and parcours.is_valid():
        parcours.save()
        messages.success(request, "Votre parcours est enregistré.")
        return redirect("membres:profil")
    return render(request, "membres/profil.html", {"parcours": parcours})
