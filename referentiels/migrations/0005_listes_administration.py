"""
Migration de DONNÉES : crée les types de contrat et les secteurs de départ (#39).

Comme pour la 0002, les listes sont RECOPIÉES ici, et non importées de `referentiels/donnees.py` :
une migration doit toujours donner le même résultat. Les listes se modifient ensuite dans le
back-office ; pour changer la liste de départ, on écrit une NOUVELLE migration.
Les tags commencent vides : ils se créent dans le back-office.
"""

from django.db import migrations

TYPES_DE_CONTRAT = [
    "Alternance",
    "CDD",
    "CDI",
    "Indépendant",
    "Intérim",
    "Stage",
    "Volontariat (VIE, service civique)",
]

SECTEURS = [
    "Assurance",
    "Banque",
    "Commerce",
    "Communication et marketing",
    "Comptabilité et audit",
    "Conseil",
    "Enseignement et formation",
    "Fonction publique",
    "Immobilier",
    "Industrie",
    "Informatique et numérique",
    "Santé et social",
    "Tourisme et hôtellerie",
    "Transport et logistique",
]


def creer(apps, schema_editor):
    for nom in TYPES_DE_CONTRAT:
        apps.get_model("referentiels", "TypeDeContrat").objects.get_or_create(nom=nom)
    for nom in SECTEURS:
        apps.get_model("referentiels", "Secteur").objects.get_or_create(nom=nom)


def supprimer(apps, schema_editor):
    """Pour revenir en arrière (`migrate referentiels 0004`) : on retire ce qu'on a créé."""
    TypeDeContrat = apps.get_model("referentiels", "TypeDeContrat")
    TypeDeContrat.objects.filter(nom__in=TYPES_DE_CONTRAT).delete()
    apps.get_model("referentiels", "Secteur").objects.filter(nom__in=SECTEURS).delete()


class Migration(migrations.Migration):
    dependencies = [("referentiels", "0004_referentiels_administration")]

    operations = [migrations.RunPython(creer, supprimer)]
