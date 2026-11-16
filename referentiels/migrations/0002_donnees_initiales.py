"""
Migration de DONNÉES : crée les 2 sites, 2 niveaux et 20 diplômes de départ.

Les listes sont RECOPIÉES ici, et non importées de `referentiels/donnees.py` : une migration
doit donner le même résultat sur une base neuve et sur une base existante, même si
`donnees.py` change plus tard. Pour renommer ou ajouter un diplôme, on modifie `donnees.py`
ET on écrit une NOUVELLE migration ; on ne touche jamais à celle-ci.
Le test `test_la_migration_cree_2_sites_2_niveaux_et_20_diplomes` signale tout écart entre
cette migration (et les suivantes) et `donnees.py`.
"""

from django.db import migrations

SITES = ["ENC Bessières", "ENC Bessières Apprentissage"]

DIPLOMES_PAR_NIVEAU = {
    "BTS": [
        "BTS ASSURANCE",
        "BTS CG",
        "BTS CI",
        "BTS COMMUNICATION",
        "BTS GPME",
        "BTS MCO",
        "BTS NDRC",
        "BTS PIM",
        "BTS SAM",
        "BTS SIO",
        "BTS TOURISME",
    ],
    "Prépa": ["ATS", "D1", "D2", "DCG", "DCG2", "DCG3", "DSCG", "ECG", "ECT"],
}


def creer(apps, schema_editor):
    # Les modèles « historiques », tels qu'ils étaient à cette migration (règle de Django).
    Site = apps.get_model("referentiels", "Site")
    Niveau = apps.get_model("referentiels", "Niveau")
    Diplome = apps.get_model("referentiels", "Diplome")
    for nom in SITES:
        Site.objects.get_or_create(nom=nom)
    for nom_niveau, diplomes in DIPLOMES_PAR_NIVEAU.items():
        niveau, _ = Niveau.objects.get_or_create(nom=nom_niveau)
        for nom in diplomes:
            Diplome.objects.get_or_create(nom=nom, defaults={"niveau": niveau})


def supprimer(apps, schema_editor):
    """Pour revenir en arrière (`migrate referentiels 0001`) : on retire ce qu'on a créé."""
    tous_les_diplomes = [nom for noms in DIPLOMES_PAR_NIVEAU.values() for nom in noms]
    apps.get_model("referentiels", "Diplome").objects.filter(nom__in=tous_les_diplomes).delete()
    apps.get_model("referentiels", "Niveau").objects.filter(nom__in=DIPLOMES_PAR_NIVEAU).delete()
    apps.get_model("referentiels", "Site").objects.filter(nom__in=SITES).delete()


class Migration(migrations.Migration):
    dependencies = [("referentiels", "0001_initial")]

    operations = [migrations.RunPython(creer, supprimer)]
