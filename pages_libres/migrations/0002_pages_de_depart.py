"""Crée les pages de départ. Leur texte reste « À COMPLÉTER par l'ENC » : pas de Lorem ipsum."""

from django.db import migrations

TEXTE_DE_DEPART = "À COMPLÉTER par l'ENC"

PAGES = [
    ("a-propos", "À propos"),
    ("mentions-legales", "Mentions légales"),
    ("cgu", "Conditions générales d'utilisation"),
    ("confidentialite", "Politique de confidentialité"),
    ("charte-du-mentorat", "Charte du mentorat"),
]


def creer_pages(apps, schema_editor):
    Page = apps.get_model("pages_libres", "Page")
    for slug, titre in PAGES:
        Page.objects.get_or_create(
            slug=slug,
            defaults={"titre": titre, "contenu": TEXTE_DE_DEPART, "publiee": True},
        )


class Migration(migrations.Migration):
    dependencies = [("pages_libres", "0001_initial")]

    operations = [migrations.RunPython(creer_pages, migrations.RunPython.noop)]