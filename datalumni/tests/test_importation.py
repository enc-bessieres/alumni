"""Import des membres de Datalumni et de leurs comptes (issue #37)."""

import json
import tempfile
import uuid
from io import StringIO
from pathlib import Path

from allauth.account.models import EmailAddress
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.management import CommandError, call_command
from django.test import TestCase

from datalumni.export_factice import FORMAT, generer_export_factice
from datalumni.importation import importer
from membres.models import Membre

ANCIEN_MOT_DE_PASSE = "ancien-mot-de-passe-datalumni"
# Comme chez Datalumni : pbkdf2_sha256, ici avec peu d'itérations pour aller vite.
EMPREINTE = PBKDF2PasswordHasher().encode(ANCIEN_MOT_DE_PASSE, "selDeTest", 1000)


def membre_export(**modifications):
    """Un membre de l'export, au format de docs/migration/export-factice.md."""
    membre = {
        "uuid": str(uuid.uuid4()),
        "email": "ines.martin.1@exemple.test",
        "email_verifie": True,
        "password": EMPREINTE,
        "origine": "import",
        "date_inscription": "2025-04-14T09:12:47Z",
        "derniere_connexion": "2026-02-03T18:30:05Z",
        "statut": "accepte",
        "visible_annuaire": True,
        "categorie": "Équipe administrative",
        "metadata": {"civilite": "Mme", "prenom": "Inès", "nom": "Martin", "nom_naissance": None},
        "groupes": [],
    }
    membre.update(modifications)
    return membre


def export(*membres):
    return {"format": FORMAT, "groupes": [], "membres": list(membres)}


class ImportTests(TestCase):
    def test_cree_le_membre_et_convertit_les_champs(self):
        donnees = membre_export()
        resume = importer(export(donnees))

        self.assertEqual((resume.crees, resume.mis_a_jour, resume.ignores), (1, 0, []))
        membre = Membre.objects.get()
        self.assertEqual(str(membre.legacy_id), donnees["uuid"])
        self.assertEqual(membre.categorie, Membre.Categorie.ADMINISTRATIF)
        self.assertEqual(membre.statut_inscription, Membre.StatutInscription.VALIDEE)
        self.assertEqual(membre.civilite, Membre.Civilite.MADAME)
        self.assertTrue(membre.visible_dans_annuaire)
        self.assertEqual(membre.cree_le.isoformat(), "2025-04-14T09:12:47+00:00")

    def test_le_membre_se_connecte_avec_son_ancien_mot_de_passe(self):
        importer(export(membre_export()))

        reponse = self.client.post(
            "/compte/login/",
            {"login": "ines.martin.1@exemple.test", "password": ANCIEN_MOT_DE_PASSE},
        )

        self.assertRedirects(reponse, "/", fetch_redirect_response=False)
        # Django ré-enregistre l'empreinte avec le nombre d'itérations actuel.
        self.assertFalse(Membre.objects.get().password.startswith("pbkdf2_sha256$1000$"))

    def test_relancer_l_import_ne_cree_pas_de_doublon(self):
        donnees = membre_export()
        importer(export(donnees))
        donnees["metadata"]["nom"] = "Martin-Durand"

        resume = importer(export(donnees))

        self.assertEqual((resume.crees, resume.mis_a_jour), (0, 1))
        self.assertEqual(Membre.objects.get().nom, "Martin-Durand")
        self.assertEqual(EmailAddress.objects.count(), 1)

    def test_un_compte_jamais_active_n_a_pas_de_mot_de_passe_utilisable(self):
        importer(export(membre_export(password="!" + "x" * 40, email_verifie=False)))

        membre = Membre.objects.get()
        self.assertFalse(membre.has_usable_password())
        self.assertFalse(EmailAddress.objects.get(user=membre).verified)

    def test_l_adresse_est_mise_en_minuscules_et_verifiee(self):
        importer(export(membre_export(email="Ines.MARTIN.1@Exemple.test")))

        adresse = EmailAddress.objects.get()
        self.assertEqual(adresse.email, "ines.martin.1@exemple.test")
        self.assertTrue(adresse.verified and adresse.primary)

    def test_un_compte_sans_e_mail_est_ignore_et_signale(self):
        donnees = membre_export(email="")

        resume = importer(export(donnees))

        self.assertEqual(Membre.objects.count(), 0)
        self.assertEqual(
            resume.ignores, [(donnees["uuid"], "pas d'adresse e-mail (elle est obligatoire)")]
        )

    def test_une_adresse_deja_utilisee_sur_le_site_n_est_pas_touchee(self):
        inscrit = Membre.objects.create_user(
            "ines.martin.1@exemple.test", "nouveau-mot-de-passe", prenom="Inès", nom="Martin"
        )

        resume = importer(export(membre_export(email="INES.MARTIN.1@exemple.test")))

        self.assertEqual(Membre.objects.count(), 1)
        self.assertEqual(len(resume.ignores), 1)
        inscrit.refresh_from_db()
        self.assertIsNone(inscrit.legacy_id)
        self.assertTrue(inscrit.check_password("nouveau-mot-de-passe"))

    def test_une_categorie_inconnue_est_ignoree(self):
        resume = importer(export(membre_export(categorie="Parent d'élève")))

        self.assertEqual(Membre.objects.count(), 0)
        self.assertIn("catégorie inconnue", resume.ignores[0][1])

    def test_tout_ou_rien(self):
        abime = membre_export(email="autre@exemple.test")
        del abime["metadata"]  # un export abîmé : l'erreur doit tout annuler

        with self.assertRaises(KeyError):
            importer(export(membre_export(), abime))

        self.assertEqual(Membre.objects.count(), 0)

    def test_l_export_factice_complet(self):
        complet = generer_export_factice()

        premier = importer(complet)
        second = importer(complet)

        # Les membres sans e-mail (5 avec les cas difficiles de #36) sont ignorés, tous les
        # autres sont importés.
        sans_email = sum(1 for m in complet["membres"] if not m["email"])
        importes = len(complet["membres"]) - sans_email
        self.assertEqual((premier.crees, len(premier.ignores)), (importes, sans_email))
        self.assertEqual((second.crees, second.mis_a_jour), (0, importes))
        visibles = [m for m in complet["membres"] if m["visible_annuaire"] and m["email"]]
        self.assertEqual(Membre.objects.filter(visible_dans_annuaire=True).count(), len(visibles))


class CommandeImporterDatalumniTests(TestCase):
    def lancer(self, contenu):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "export.json"
            fichier.write_text(json.dumps(contenu), encoding="utf-8")
            sortie = StringIO()
            call_command("importer_datalumni", str(fichier), stdout=sortie)
            return sortie.getvalue()

    def test_affiche_le_resume_sans_donnee_personnelle(self):
        sans_email = membre_export(email="")

        sortie = self.lancer(export(membre_export(), sans_email))

        self.assertIn("1 membres créés, 0 mis à jour, 1 ignorés.", sortie)
        self.assertIn(sans_email["uuid"], sortie)
        self.assertNotIn("Martin", sortie)  # ni nom ni e-mail dans le terminal

    def test_refuse_un_fichier_d_un_autre_format(self):
        with self.assertRaises(CommandError):
            self.lancer({"format": "autre-chose", "membres": [membre_export()]})
        self.assertEqual(Membre.objects.count(), 0)

    def test_refuse_un_fichier_introuvable(self):
        with self.assertRaises(CommandError):
            call_command("importer_datalumni", "exports/n-existe-pas.json")
