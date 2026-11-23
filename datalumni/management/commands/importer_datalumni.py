"""
Importe les membres de Datalumni et leurs comptes, depuis un export JSON.

    python manage.py importer_datalumni exports/datalumni-factice.json

Rejouable : un membre est retrouvé par son identifiant Datalumni, jamais créé deux fois.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from datalumni.export_factice import FORMAT
from datalumni.importation import importer


class Command(BaseCommand):
    help = "Importe les membres de Datalumni et leurs comptes depuis un export JSON."

    def add_arguments(self, parser):
        parser.add_argument("fichier", help="l'export JSON de Datalumni")

    def handle(self, *args, fichier, **options):
        chemin = Path(fichier)
        if not chemin.exists():
            raise CommandError(f"Fichier introuvable : {chemin}")
        export = json.loads(chemin.read_text(encoding="utf-8"))
        # Le format du vrai export est encore une hypothèse : on refuse un fichier inattendu
        # plutôt que d'importer n'importe quoi.
        if export.get("format") != FORMAT:
            raise CommandError(f"Format inattendu : {export.get('format')!r} (attendu : {FORMAT})")

        resume = importer(export)

        self.stdout.write(
            self.style.SUCCESS(
                f"{resume.crees} membres créés, {resume.mis_a_jour} mis à jour, "
                f"{len(resume.ignores)} ignorés."
            )
        )
        # Seulement l'identifiant Datalumni et la raison : sur le vrai export, ce sont des
        # données personnelles, elles ne doivent pas s'afficher dans un terminal.
        for identifiant, raison in resume.ignores:
            self.stdout.write(f"  ignoré {identifiant} : {raison}")
