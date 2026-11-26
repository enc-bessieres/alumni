"""
Export factice au format du vrai directory.csv (docs/migration/export-reel.md, issue #84).
Ces tests n'ont pas besoin de la base de données.
"""

from collections import Counter

from django.test import SimpleTestCase

from datalumni.export_factice import COLONNES, SECTEURS, generer_export_factice
from referentiels.donnees import DIPLOMES, SITES


class ExportFacticeTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lignes = generer_export_factice()

    def remplies(self, colonne):
        return sum(1 for ligne in self.lignes if ligne[colonne])

    def vraies(self, colonne):
        return sum(1 for ligne in self.lignes if ligne[colonne] == "True")

    # --- Le fichier dans son ensemble ----------------------------------------------------

    def test_meme_graine_meme_export_autre_graine_autre_export(self):
        self.assertEqual(generer_export_factice(), self.lignes)
        self.assertNotEqual(generer_export_factice(7)[0]["user_id"], self.lignes[0]["user_id"])

    def test_les_28_colonnes_du_vrai_export(self):
        self.assertEqual(len(COLONNES), 28)
        self.assertTrue(all(list(ligne) == COLONNES for ligne in self.lignes))

    def test_les_volumes_de_l_export_reel(self):
        # Colonne : nombre de cases remplies, relevé dans docs/migration/export-reel.md.
        attendus = {
            "user_id": 6138, "external_ref": 0, "first_name": 6134, "birth_name": 55,
            "civility": 1242, "location": 663, "phone": 996, "current_position": 357,
            "business_sector": 340, "last_login": 1252, "last_profile_update": 5744,
            "account_activation_date": 1233, "category": 6133, "campus": 4978, "degree": 5701,
            "promotion_year": 5691, "import_date": 5683, "job_search": 289, "mentoring_role": 282,
        }  # fmt: skip
        self.assertEqual({c: self.remplies(c) for c in attendus}, attendus)
        self.assertEqual(self.vraies("account_status"), 1233)
        self.assertEqual(self.vraies("visibility_directory"), 6129)  # toujours True

    def test_adresses_toutes_en_test_et_toutes_differentes(self):
        adresses = [ligne["email"] for ligne in self.lignes]
        self.assertTrue(all(a.endswith(".test") for a in adresses))  # règle 1 d'AGENTS.md
        self.assertEqual(len(set(adresses)), len(adresses))
        self.assertTrue(all(a == a.lower() for a in adresses))
        etudiants = sum(a.endswith("@enc-bessieres.exemple.test") for a in adresses)
        self.assertEqual(etudiants, 2048)

    def test_telephones_dans_la_plage_reservee_a_la_fiction(self):
        telephones = [ligne["phone"] for ligne in self.lignes if ligne["phone"]]
        self.assertTrue(all(t.startswith("+3363998") and len(t) == 12 for t in telephones))

    def test_identifiants_uniques_et_aucun_mot_de_passe(self):
        identifiants = [ligne["user_id"] for ligne in self.lignes]
        self.assertEqual(len(set(identifiants)), 6138)
        self.assertNotIn("password", COLONNES)  # Datalumni ne fournit pas les mots de passe

    # --- Les cas à traiter par l'import --------------------------------------------------

    def test_les_comptes_actives_par_categorie(self):
        actives = Counter(
            ligne["category"] for ligne in self.lignes if ligne["account_status"] == "True"
        )
        self.assertEqual(
            (actives["Alumni"], actives["Enseignant"], actives["Recruteur"]), (1143, 43, 17)
        )
        # Un compte inscrit seul (import_date vide) est forcément activé.
        seuls = [ligne for ligne in self.lignes if not ligne["import_date"]]
        self.assertEqual(len(seuls), 455)
        self.assertTrue(all(ligne["account_status"] == "True" for ligne in seuls))

    def test_noms_en_majuscules_et_128_groupes_d_homonymes(self):
        noms = [ligne["last_name"] for ligne in self.lignes if ligne["last_name"]]
        self.assertEqual(sum(n == n.upper() for n in noms), 6036)
        identites = Counter(
            (ligne["first_name"], ligne["last_name"].upper())
            for ligne in self.lignes
            if ligne["first_name"]
        )
        groupes = [n for n in identites.values() if n > 1]
        self.assertEqual((len(groupes), sum(groupes)), (128, 259))

    def test_categories_sites_et_diplomes_doubles_separes_par_une_barre(self):
        self.assertEqual(sum(" / " in ligne["category"] for ligne in self.lignes), 12)
        self.assertEqual(sum(ligne["campus"] == " / ".join(SITES) for ligne in self.lignes), 52)
        plusieurs = [ligne for ligne in self.lignes if " / " in ligne["degree"]]
        self.assertEqual(len(plusieurs), 121)
        connus = {d for noms in DIPLOMES.values() for d in noms}
        diplomes = {
            d for ligne in self.lignes if ligne["degree"] for d in ligne["degree"].split(" / ")
        }
        self.assertLessEqual(diplomes, connus)

    def test_une_seule_promo_de_1963_a_2029(self):
        annees = [int(ligne["promotion_year"]) for ligne in self.lignes if ligne["promotion_year"]]
        self.assertEqual((min(annees), max(annees)), (1963, 2029))
        self.assertTrue(all(ligne["degree"] for ligne in self.lignes if ligne["promotion_year"]))

    def test_civilites_secteurs_et_mentorat_tels_que_datalumni_les_ecrit(self):
        civilites = {ligne["civility"] for ligne in self.lignes} - {""}
        self.assertEqual(civilites, {"Mme.", "M.", "Madame", "Monsieur", "Non renseigné"})
        secteurs = {ligne["business_sector"] for ligne in self.lignes} - {""}
        self.assertLessEqual(secteurs, set(SECTEURS))
        self.assertEqual(len(SECTEURS), 26)
        roles = Counter(ligne["mentoring_role"] for ligne in self.lignes if ligne["mentoring_role"])
        self.assertEqual(roles, {"mentor": 166, "mentee": 103, "mentor / mentee": 13})
