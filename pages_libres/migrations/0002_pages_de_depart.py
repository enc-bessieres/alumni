"""Crée les pages légales de départ, avec un contenu « À COMPLÉTER » visible (règle 6)."""

from django.db import migrations

PAGES = [
    ("a-propos", "À propos"),
    ("mentions-legales", "Mentions légales"),
    ("cgu", "Conditions générales d'utilisation"),
    ("confidentialite", "Politique de confidentialité"),
]


def creer_pages(apps, schema_editor):
    Page = apps.get_model("pages_libres", "Page")
    for slug, titre in PAGES:
        Page.objects.get_or_create(
            slug=slug,
            defaults={
                "titre": titre,
                "contenu": f"À COMPLÉTER : texte de la page « {titre} », propre à l'ENC Bessières.",
                "publiee": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("pages_libres", "0001_initial")]

    operations = [migrations.RunPython(creer_pages, migrations.RunPython.noop)]