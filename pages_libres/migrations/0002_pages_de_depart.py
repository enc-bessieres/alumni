"""Crée les pages de départ. Leur texte reste « À COMPLÉTER par l'ENC » : pas de Lorem ipsum."""

from django.db import migrations

PAGES = [
    (
        "a-propos",
        "À propos",
        "À COMPLÉTER : présentation de l'association des anciens élèves, fournie par l'ENC",
    ),
    (
        "mentions-legales",
        "Mentions légales",
        "À COMPLÉTER : texte des mentions légales, fourni par l'ENC",
    ),
    (
        "cgu",
        "Conditions générales d'utilisation",
        "À COMPLÉTER : conditions générales d'utilisation, fournies par l'ENC",
    ),
    (
        "confidentialite",
        "Politique de confidentialité",
        "À COMPLÉTER : politique de confidentialité, fournie par l'ENC avec le DPO",
    ),
    (
        "charte-du-mentorat",
        "Charte du mentorat",
        "À COMPLÉTER : charte du mentorat, fournie par l'ENC",
    ),
]


def creer_pages(apps, schema_editor):
    Page = apps.get_model("pages_libres", "Page")
    for slug, titre, contenu in PAGES:
        Page.objects.get_or_create(
            slug=slug,
            defaults={"titre": titre, "contenu": contenu, "publiee": True},
        )


class Migration(migrations.Migration):
    dependencies = [("pages_libres", "0001_initial")]

    operations = [migrations.RunPython(creer_pages, migrations.RunPython.noop)]