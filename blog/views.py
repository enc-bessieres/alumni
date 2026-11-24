from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from membres.droits import reserve_aux_membres_valides

from .forms import ArticleForm, SignalementForm
from .models import Article, Signalement


def detail(request, slug):
    article = get_object_or_404(Article, slug=slug, statut=Article.Statut.PUBLIE)
    return render(request, "blog/detail.html", {"article": article})


def liste(request):
    articles = Article.objects.filter(statut=Article.Statut.PUBLIE)
    return render(request, "blog/liste.html", {"articles": articles})


def adresse_unique(titre):
    """Calcule une adresse à partir du titre, en ajoutant -2, -3… si elle est déjà prise."""
    base = slugify(titre)[:40] or "article"
    adresse = base
    numero = 2
    while Article.objects.filter(slug=adresse).exists():
        adresse = f"{base}-{numero}"
        numero += 1
    return adresse


@reserve_aux_membres_valides
def ecrire(request):
    if request.method == "POST":
        formulaire = ArticleForm(request.POST)
        if formulaire.is_valid():
            article = formulaire.save(commit=False)
            article.auteur = request.user
            article.statut = Article.Statut.PUBLIE
            article.slug = adresse_unique(article.titre)
            article.save()
            messages.success(request, "Merci ! Votre article est publié.")
            return redirect(article)
    else:
        formulaire = ArticleForm()
    return render(request, "blog/ecrire.html", {"formulaire": formulaire})


@require_POST
@reserve_aux_membres_valides
def signaler(request, slug):
    article = get_object_or_404(Article, slug=slug, statut=Article.Statut.PUBLIE)
    formulaire = SignalementForm(request.POST)
    if formulaire.is_valid():
        _, cree = Signalement.objects.get_or_create(
            article=article,
            membre=request.user,
            defaults={"motif": formulaire.cleaned_data["motif"]},
        )
        if cree:
            messages.success(request, "Merci, l'équipe va vérifier cet article.")
        else:
            messages.info(request, "Vous avez déjà signalé cet article.")
    return redirect(article)
