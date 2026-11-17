"""
Passe le contenu des pages existantes du texte brut au HTML.

Le champ contenu utilise maintenant l'éditeur de texte (texte_riche) : il attend du HTML.
On convertit le texte comme le faisait le gabarit avec |linebreaks (texte échappé,
paragraphes <p>), puis on le nettoie avec la même liste que l'éditeur.
"""

from django.db import migrations
from django.utils.html import linebreaks

from texte_riche.champs import nettoyer


def texte_vers_html(apps, schema_editor):
    Page = apps.get_model("pages_libres", "Page")
    for page in Page.objects.all():
        page.contenu = nettoyer(linebreaks(page.contenu, autoescape=True))
        page.save(update_fields=["contenu"])


class Migration(migrations.Migration):
    dependencies = [("pages_libres", "0002_pages_de_depart")]

    operations = [migrations.RunPython(texte_vers_html, migrations.RunPython.noop)]