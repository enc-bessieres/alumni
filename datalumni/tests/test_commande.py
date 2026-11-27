"""La commande `manage.py generer_export_factice`."""

import csv
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase

from datalumni.export_factice import COLONNES


class CommandeGenererExportFacticeTests(SimpleTestCase):
    def test_ecrit_un_csv_comme_le_vrai_export(self):
        with tempfile.TemporaryDirectory() as dossier:
            sortie = Path(dossier) / "sous-dossier" / "directory.csv"
            messages = StringIO()
            call_command("generer_export_factice", sortie=str(sortie), stdout=messages)

            octets = sortie.read_bytes()
            self.assertTrue(octets.startswith(b"\xef\xbb\xbf"))  # UTF-8 avec BOM, comme Datalumni
            with open(sortie, encoding="utf-8-sig", newline="") as fichier:
                lecteur = csv.DictReader(fichier)
                lignes = list(lecteur)
            self.assertEqual(lecteur.fieldnames, COLONNES)
            self.assertEqual(len(lignes), 6138)
            self.assertIn("Équipe administrative", octets.decode("utf-8-sig"))
            self.assertIn("6138 comptes", messages.getvalue())
