"""
Annuaire : le choix « visible dans l'annuaire », et l'extension unaccent de PostgreSQL.

unaccent permet de chercher « lea » et de trouver « Léa ». C'est une extension « de confiance »
depuis PostgreSQL 13 : le propriétaire de la base peut l'installer, sans superutilisateur.
"""

from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("membres", "0004_libelle_gerer_les_droits"),
    ]

    operations = [
        UnaccentExtension(),
        migrations.AddField(
            model_name="membre",
            name="visible_dans_annuaire",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Choisi par le membre : nom, catégorie et diplômes visibles des membres "
                    "validés."
                ),
                verbose_name="visible dans l'annuaire",
            ),
        ),
    ]
