from django.shortcuts import get_object_or_404, render

from .models import Article


def detail(request, slug):
    article = get_object_or_404(Article, slug=slug, statut=Article.Statut.PUBLIE)
    return render(request, "blog/detail.html", {"article": article})

def liste(request):
    articles = Article.objects.filter(statut=Article.Statut.PUBLIE)
    return render(request, "blog/liste.html", {"articles": articles})
