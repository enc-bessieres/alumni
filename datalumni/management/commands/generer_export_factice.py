"""
Écrit l'export factice de l'annuaire Datalumni, au format du vrai directory.csv (fausses données).

    python manage.py generer_export_factice
    python manage.py generer_export_factice --graine 7 --sortie exports/autre.csv
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from datalumni.export_factice import ecrire_export_factice, generer_export_factice


class Command(BaseCommand):
    help = "Écrit l'export factice de l'annuaire Datalumni (CSV) dans exports/ (non versionné)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sortie", default="exports/datalumni-factice-directory.csv", help="fichier à écrire"
        )
        parser.add_argument("--graine", type=int, default=2026, help="même graine, même export")

    def handle(self, *args, sortie, graine, **options):
        lignes = generer_export_factice(graine)
        chemin = Path(sortie)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        ecrire_export_factice(lignes, chemin)
        self.stdout.write(
            self.style.SUCCESS(f"Export factice écrit : {len(lignes)} comptes → {chemin}")
        )
