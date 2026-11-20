"""La commande `manage.py generer_export_factice`."""

import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase


class CommandeGenererExportFacticeTests(SimpleTestCase):
    def test_ecrit_un_json_lisible_avec_les_accents(self):
        with tempfile.TemporaryDirectory() as dossier:
            sortie = Path(dossier) / "sous-dossier" / "export.json"
            messages = StringIO()
            call_command("generer_export_factice", sortie=str(sortie), stdout=messages)

            contenu = sortie.read_text(encoding="utf-8")
            export = json.loads(contenu)
            self.assertEqual(export["format"], "datalumni-factice/1")
            self.assertEqual(len(export["membres"]), 1300)
            self.assertIn("Équipe administrative", contenu)  # et non « Équipe »
            self.assertIn("1300 membres", messages.getvalue())
