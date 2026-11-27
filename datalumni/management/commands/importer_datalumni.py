"""
Importe l'annuaire de Datalumni (directory.csv) : un compte par ligne.

    python manage.py importer_datalumni exports/datalumni-factice-directory.csv

Rejouable : un membre est retrouvé par son identifiant Datalumni, jamais créé deux fois.
"""

import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from datalumni.importation import FormatInattendu, importer, lire_csv


class Command(BaseCommand):
    help = "Importe l'annuaire de Datalumni (directory.csv) : un compte par ligne."

    def add_arguments(self, parser):
        parser.add_argument("fichier", help="le directory.csv de Datalumni, ou l'export factice")

    def handle(self, *args, fichier, **options):
        chemin = Path(fichier)
        if not chemin.exists():
            raise CommandError(f"Fichier introuvable : {chemin}")
        try:
            lignes = lire_csv(chemin)
        except FormatInattendu as erreur:
            raise CommandError(f"Ce n'est pas un directory.csv de Datalumni : {erreur}") from None

        debut = time.monotonic()
        resume = importer(lignes)
        duree = time.monotonic() - debut

        self.stdout.write(
            self.style.SUCCESS(
                f"{resume.crees} membres créés, {resume.mis_a_jour} mis à jour, "
                f"{len(resume.ignores)} ignorés, en {duree:.0f} s."
            )
        )
        if resume.deja_venus:
            self.stdout.write(
                f"{resume.deja_venus} déjà venus sur le nouveau site : non modifiés par l'import."
            )
        # Seulement l'identifiant Datalumni et la raison : sur le vrai export, noms et e-mails
        # sont des données personnelles, ils n'ont rien à faire dans un terminal.
        for identifiant, raison in resume.ignores:
            self.stdout.write(f"  ignoré {identifiant} : {raison}")
