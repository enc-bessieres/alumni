"""
Écrit l'export factice au format Datalumni (fausses données uniquement).

    python manage.py generer_export_factice
    python manage.py generer_export_factice --graine 7 --sortie exports/autre.json
"""

import json
from dataclasses import replace
from pathlib import Path

from django.core.management.base import BaseCommand

from datalumni.export_factice import CONFIG_PAR_DEFAUT, generer_export_factice


class Command(BaseCommand):
    help = "Écrit l'export factice au format Datalumni dans exports/ (dossier non versionné)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sortie", default="exports/datalumni-factice.json", help="fichier à écrire"
        )
        parser.add_argument(
            "--graine", type=int, default=CONFIG_PAR_DEFAUT.graine, help="même graine, même export"
        )

    def handle(self, *args, sortie, graine, **options):
        export = generer_export_factice(replace(CONFIG_PAR_DEFAUT, graine=graine))
        chemin = Path(sortie)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        # ensure_ascii=False : les accents restent lisibles dans le fichier.
        contenu = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
        chemin.write_text(contenu, encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"Export factice écrit : {len(export['groupes'])} groupes, "
                f"{len(export['membres'])} membres → {chemin}"
            )
        )
