from django.shortcuts import get_object_or_404, render

from .models import Page


def detail(request, slug):
    """Affiche une page publiée ; une page non publiée ou inconnue donne une 404."""
    page = get_object_or_404(Page, slug=slug, publiee=True)
    return render(request, "pages_libres/detail.html", {"page": page})
