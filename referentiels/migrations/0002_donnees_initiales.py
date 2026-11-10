"""
Migration de DONNÉES : crée les 2 sites, 2 niveaux et 20 diplômes de `referentiels/donnees.py`.

Elle tourne une fois par base, comme toute migration, y compris dans la base de test.
Si la liste change plus tard (un nouveau diplôme), on écrit une NOUVELLE migration : on ne
modifie jamais une migration déjà appliquée chez les autres.
"""

from django.db import migrations

from referentiels.creation import creer_referentiels
from referentiels.donnees import DIPLOMES, NIVEAUX, SITES


def creer(apps, schema_editor):
    # Les modèles « historiques », tels qu'ils étaient à cette migration (règle de Django).
    creer_referentiels(
        apps.get_model("referentiels", "Site"),
        apps.get_model("referentiels", "Niveau"),
        apps.get_model("referentiels", "Diplome"),
    )


def supprimer(apps, schema_editor):
    """Pour revenir en arrière (`migrate referentiels 0001`) : on retire ce qu'on a créé."""
    tous_les_diplomes = [nom for noms in DIPLOMES.values() for nom in noms]
    apps.get_model("referentiels", "Diplome").objects.filter(nom__in=tous_les_diplomes).delete()
    apps.get_model("referentiels", "Niveau").objects.filter(nom__in=NIVEAUX).delete()
    apps.get_model("referentiels", "Site").objects.filter(nom__in=SITES).delete()


class Migration(migrations.Migration):
    dependencies = [("referentiels", "0001_initial")]

    operations = [migrations.RunPython(creer, supprimer)]
