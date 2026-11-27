"""
Charge la liste de départ des mots interdits (décision de #43).

Liste générée par une IA, à relire et compléter par l'ENC dans le back-office.
Elle est recopiée ici et figée : une migration doit toujours donner le même résultat.
"""

from django.db import migrations

MOTS = [
    "andouille de merde",
    "baltringue",
    "branleur",
    "branleuse",
    "branquignol",
    "casse-couilles",
    "casse-bonbons",
    "connard",
    "connasse",
    "conne",
    "connerie",
    "couillon",
    "couillonne",
    "crétin",
    "crétine",
    "dégénéré",
    "dégénérée",
    "enculé",
    "enculée",
    "enfoiré",
    "enfoirée",
    "emmerdeur",
    "emmerdeuse",
    "emmerder",
    "emmerdement",
    "fdp",
    "fils de pute",
    "foutre",
    "garce",
    "glandu",
    "gogol",
    "grognasse",
    "imbécile",
    "lopette",
    "merde",
    "merdeux",
    "merdeuse",
    "merdique",
    "naze",
    "nègre",
    "pétasse",
    "pouffiasse",
    "pute",
    "putain",
    "putain de merde",
    "raclure",
    "racaille",
    "salaud",
    "salaude",
    "salope",
    "schlag",
    "sous-merde",
    "suceur",
    "suceuse",
    "tapette",
    "tocard",
    "trouduc",
    "trou du cul",
    "tête de con",
    "va te faire foutre",
    "va te faire enculer",
    "zgeg",
    "zob",
    "bite",
    "couille",
    "chier",
    "chiant",
    "chiante",
    "nique",
    "niquer",
    "nique ta mère",
    "nique ta race",
    "nique ta gueule",
    "tg",
    "ntm",
    "ta gueule",
    "ferme ta gueule",
    "ferme ton clapet",
    "casse-toi",
]


def charger(apps, schema_editor):
    MotInterdit = apps.get_model("moderation", "MotInterdit")
    for mot in MOTS:
        MotInterdit.objects.get_or_create(mot=mot.strip().lower())


class Migration(migrations.Migration):
    dependencies = [("moderation", "0001_initial")]

    operations = [migrations.RunPython(charger, migrations.RunPython.noop)]