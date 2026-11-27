from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from membres.droits import est_membre_valide, reserve_aux_membres_valides

from .forms import ArticleForm
from .models import Article


def detail(request, slug):
    article = get_object_or_404(Article, slug=slug, statut=Article.Statut.PUBLIE)
    return render(request, "blog/detail.html", {"article": article})


def liste(request):
    articles = Article.objects.filter(statut=Article.Statut.PUBLIE)
    peut_ecrire = est_membre_valide(request.user)
    return render(request, "blog/liste.html", {"articles": articles, "peut_ecrire": peut_ecrire})


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
