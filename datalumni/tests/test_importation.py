"""Import de l'annuaire Datalumni au format CSV réel (issue #84)."""

import tempfile
import uuid
from io import StringIO
from pathlib import Path

from allauth.account.models import EmailAddress
from django.core.management import CommandError, call_command
from django.test import TestCase

from datalumni.export_factice import COLONNES, ecrire_export_factice, generer_export_factice
from datalumni.importation import FormatInattendu, importer, lire_csv
from membres.models import Membre


def ligne(**modifications):
    """Une ligne de directory.csv, au format de docs/migration/export-reel.md."""
    return (
        dict.fromkeys(COLONNES, "")
        | {
            "user_id": str(uuid.uuid4()),
            "first_name": "Inès",
            "last_name": "MARTIN",
            "email": "ines.martin.1@exemple.test",
            "civility": "Mme.",
            "account_status": "True",
            "category": "Alumni",
            "visibility_directory": "True",
            "import_date": "2025-04-14",  # une date seule, comme dans le vrai fichier
            "last_login": "2026-02-03T18:30:05+00:00",
        }
        | modifications
    )


class ImportTests(TestCase):
    def test_cree_le_membre_et_convertit_les_champs(self):
        donnees = ligne()

        resume = importer([donnees])

        self.assertEqual((resume.crees, resume.mis_a_jour, resume.ignores), (1, 0, []))
        membre = Membre.objects.get()
        self.assertEqual(str(membre.legacy_id), donnees["user_id"])
        self.assertEqual((membre.prenom, membre.nom), ("Inès", "MARTIN"))  # gardé tel quel
        self.assertEqual(membre.civilite, Membre.Civilite.MADAME)
        self.assertEqual(membre.categorie, Membre.Categorie.ALUMNI)
        self.assertEqual(membre.statut_inscription, Membre.StatutInscription.VALIDEE)
        self.assertTrue(membre.visible_dans_annuaire)
        self.assertEqual(membre.cree_le.isoformat(), "2025-04-14T00:00:00+00:00")
        self.assertFalse(membre.has_usable_password())  # Datalumni ne donne pas les mots de passe
        adresse = EmailAddress.objects.get(user=membre)
        self.assertEqual(
            (adresse.email, adresse.primary, adresse.verified), (membre.email, True, False)
        )

    def test_relancer_met_a_jour_un_compte_pas_encore_venu_sans_doublon(self):
        donnees = ligne()
        importer([donnees])
        donnees["last_name"] = "MARTIN-DURAND"

        resume = importer([donnees])

        self.assertEqual((resume.crees, resume.mis_a_jour, resume.deja_venus), (0, 1, 0))
        self.assertEqual(Membre.objects.get().nom, "MARTIN-DURAND")
        self.assertEqual(EmailAddress.objects.count(), 1)

    def test_une_relance_ne_touche_pas_un_compte_deja_venu_sur_le_site(self):
        # Le test d'Alex sur #102 : le membre a suivi le lien (#85), puis fait ses choix ici.
        lignes = generer_export_factice()[:20]
        importer(lignes)
        membre = Membre.objects.get(legacy_id=lignes[0]["user_id"])
        membre.visible_dans_annuaire = False  # retiré de l'annuaire (règle 5)
        membre.email = "nouvelle.adresse@exemple.test"
        membre.set_password("Un-mot-de-passe-2026")
        membre.save()
        EmailAddress.objects.filter(user=membre).update(email=membre.email, verified=True)

        resume = importer(lignes)

        self.assertEqual((resume.crees, resume.mis_a_jour, resume.deja_venus), (0, 19, 1))
        membre.refresh_from_db()
        self.assertFalse(membre.visible_dans_annuaire)
        self.assertEqual(membre.email, "nouvelle.adresse@exemple.test")
        self.assertTrue(membre.check_password("Un-mot-de-passe-2026"))
        adresse = EmailAddress.objects.get(user=membre)
        self.assertEqual((adresse.email, adresse.verified), (membre.email, True))

    def test_les_cinq_civilites_de_datalumni(self):
        civilites = ["Mme.", "Madame", "M.", "Monsieur", "Non renseigné"]
        lignes = [ligne(civility=c, email=f"{i}@exemple.test") for i, c in enumerate(civilites)]

        importer(lignes)

        obtenues = [Membre.objects.get(email=f"{i}@exemple.test").civilite for i in range(5)]
        self.assertEqual(obtenues, ["madame", "madame", "monsieur", "monsieur", ""])

    def test_deux_categories_la_premiere_est_gardee(self):
        importer([ligne(category="Enseignant / Équipe administrative")])

        self.assertEqual(Membre.objects.get().categorie, Membre.Categorie.ENSEIGNANT)

    def test_sans_categorie_ou_sans_nom_le_compte_est_importe(self):
        sans_categorie = ligne(category="")
        sans_nom = ligne(first_name="", last_name="", email="sans.nom@exemple.test")

        resume = importer([sans_categorie, sans_nom])

        self.assertEqual((resume.crees, resume.ignores), (2, []))

    def test_une_categorie_inconnue_est_ignoree(self):
        resume = importer([ligne(category="Parent d'élève")])

        self.assertEqual(Membre.objects.count(), 0)
        self.assertIn("catégorie inconnue", resume.ignores[0][1])

    def test_une_adresse_deja_utilisee_sur_le_site_n_est_pas_touchee(self):
        inscrit = Membre.objects.create_user(
            "ines.martin.1@exemple.test", "nouveau-mot-de-passe", prenom="Inès", nom="Martin"
        )

        resume = importer([ligne(email="INES.MARTIN.1@exemple.test")])

        self.assertEqual(Membre.objects.count(), 1)
        self.assertEqual(resume.ignores[0][1], "adresse e-mail déjà utilisée par un autre compte")
        inscrit.refresh_from_db()
        self.assertIsNone(inscrit.legacy_id)
        self.assertTrue(inscrit.check_password("nouveau-mot-de-passe"))

    def test_deux_lignes_avec_la_meme_adresse_la_seconde_est_ignoree(self):
        premiere, seconde = ligne(), ligne()

        resume = importer([premiere, seconde])

        self.assertEqual(Membre.objects.get().legacy_id, uuid.UUID(premiere["user_id"]))
        self.assertEqual(resume.ignores[0][0], seconde["user_id"])

    def test_tout_ou_rien(self):
        abimee = ligne(email="autre@exemple.test")
        del abimee["category"]  # un fichier abîmé : l'erreur doit tout annuler

        with self.assertRaises(KeyError):
            importer([ligne(), abimee])

        self.assertEqual(Membre.objects.count(), 0)

    def test_l_export_factice_complet(self):
        # Un seul import des 6138 lignes : il est lent en local. La relance est vérifiée plus haut.
        lignes = generer_export_factice()

        resume = importer(lignes)

        self.assertEqual((resume.crees, resume.ignores), (6138, []))
        visibles = sum(1 for donnees in lignes if donnees["visibility_directory"] != "False")
        self.assertEqual(Membre.objects.filter(visible_dans_annuaire=True).count(), visibles)
        self.assertFalse(Membre.objects.filter(password__startswith="pbkdf2").exists())


class LectureEtCommandeTests(TestCase):
    def ecrire(self, dossier, lignes):
        chemin = Path(dossier) / "directory.csv"
        ecrire_export_factice(lignes, chemin)
        return chemin

    def test_lit_le_csv_avec_bom_et_refuse_un_autre_format(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = self.ecrire(dossier, [ligne()])
            self.assertEqual(lire_csv(chemin)[0]["first_name"], "Inès")

            autre = Path(dossier) / "autre.csv"
            autre.write_text("nom,prenom\nMartin,Inès\n", encoding="utf-8")
            with self.assertRaises(FormatInattendu):
                lire_csv(autre)

    def test_la_commande_affiche_le_resume_sans_donnee_personnelle(self):
        sans_email = ligne(email="")
        with tempfile.TemporaryDirectory() as dossier:
            chemin = self.ecrire(dossier, [ligne(), sans_email])
            sortie = StringIO()
            call_command("importer_datalumni", str(chemin), stdout=sortie)

        texte = sortie.getvalue()
        self.assertIn("1 membres créés, 0 mis à jour, 1 ignorés", texte)
        self.assertIn(f"ignoré {sans_email['user_id']} : pas d'adresse e-mail", texte)
        self.assertNotIn("MARTIN", texte)  # ni nom ni e-mail dans le terminal
        self.assertNotIn("exemple.test", texte)

    def test_la_commande_compte_a_part_les_comptes_deja_venus(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = self.ecrire(dossier, [ligne()])
            call_command("importer_datalumni", str(chemin), stdout=StringIO())
            membre = Membre.objects.get()
            membre.set_password("Un-mot-de-passe-2026")
            membre.save()
            sortie = StringIO()
            call_command("importer_datalumni", str(chemin), stdout=sortie)

        self.assertIn("0 membres créés, 0 mis à jour, 0 ignorés", sortie.getvalue())
        self.assertIn("1 déjà venus sur le nouveau site : non modifiés", sortie.getvalue())

    def test_la_commande_refuse_un_fichier_introuvable_ou_d_un_autre_format(self):
        with self.assertRaises(CommandError):
            call_command("importer_datalumni", "exports/n-existe-pas.csv")
        with tempfile.TemporaryDirectory() as dossier:
            autre = Path(dossier) / "autre.csv"
            autre.write_text("nom\nMartin\n", encoding="utf-8")
            with self.assertRaises(CommandError):
                call_command("importer_datalumni", str(autre))
