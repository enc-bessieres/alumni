"""
Export factice au format Datalumni (docs/migration/export-factice.md).
Ces tests n'ont pas besoin de la base de données.
"""

import json
from dataclasses import replace

from django.contrib.auth.hashers import PBKDF2PasswordHasher, check_password
from django.test import SimpleTestCase

from datalumni.export_factice import CONFIG_PAR_DEFAUT, generer_export_factice
from referentiels.donnees import DIPLOMES

# Produite par Django 5.2.19 (make_password) avec un mot de passe factice.
EMPREINTE_DJANGO = "pbkdf2_sha256$1000$selCourt$aG21TaBWDeLTNSMtoroTPzcQF3l1bX7+lAimMuXMIXg="


def annees(m):
    """Les années de promo d'un membre, dans l'ordre de l'export."""
    return [g["timeline"]["annee"] for g in m["groupes"] if g["timeline"]]


class ExportFacticeTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.export = generer_export_factice()  # une seule fois : il faut environ une seconde
        cls.membres = cls.export["membres"]

    def compter(self, condition):
        return sum(1 for m in self.membres if condition(m))

    # --- L'export dans son ensemble ------------------------------------------------------

    def test_meme_graine_meme_export_autre_graine_autre_export(self):
        self.assertEqual(json.dumps(generer_export_factice()), json.dumps(self.export))
        autre = generer_export_factice(replace(CONFIG_PAR_DEFAUT, graine=1))
        self.assertNotEqual(autre["membres"][0]["uuid"], self.membres[0]["uuid"])

    def test_reprend_les_chiffres_du_releve(self):
        visibles = [m for m in self.membres if m["visible_annuaire"]]
        self.assertEqual(len(self.membres), 1300)
        self.assertEqual(len(visibles), 1222)  # somme des catégories (l'annuaire en annonce 1214)
        self.assertEqual(sum(1 for m in visibles if m["categorie"] == "Alumni"), 1143)
        self.assertEqual(sum(1 for m in visibles if m["categorie"] == "Enseignant"), 50)
        self.assertEqual(self.compter(lambda m: m["origine"] == "import"), 784)

    def test_adresses_toutes_en_test_et_toutes_differentes(self):
        adresses = [m["email"] for m in self.membres]
        self.assertTrue(all(a.endswith("@exemple.test") for a in adresses))  # règle 1
        self.assertEqual(len(set(adresses)), len(adresses))

    def test_deux_membres_ne_portent_jamais_le_meme_nom_par_hasard(self):
        noms = [(m["metadata"]["prenom"], m["metadata"]["nom"]) for m in self.membres]
        self.assertEqual(len(set(noms)), len(noms))

    def test_uuid_uniques_et_appartenances_vers_des_groupes_existants(self):
        uuids = [o["uuid"] for o in self.export["groupes"] + self.membres]
        self.assertEqual(len(set(uuids)), len(uuids))
        connus = {g["uuid"] for g in self.export["groupes"]}
        self.assertTrue(all(g["groupe_uuid"] in connus for m in self.membres for g in m["groupes"]))

    # --- Les référentiels et les promos --------------------------------------------------

    def test_reprend_les_20_diplomes_ranges_sous_leur_niveau(self):
        diplomes = [g for g in self.export["groupes"] if g["type"] == "diplome"]
        attendus = [nom for noms in DIPLOMES.values() for nom in noms]
        self.assertEqual(sorted(g["nom"] for g in diplomes), sorted(attendus))
        bts = next(g for g in self.export["groupes"] if g["type"] == "niveau" and g["nom"] == "BTS")
        sio = next(g for g in diplomes if g["nom"] == "BTS SIO")
        self.assertEqual(sio["parent_uuid"], bts["uuid"])

    def test_promos_de_1990_a_2026_sur_les_20_diplomes(self):
        alumni = [a for m in self.membres if m["categorie"] == "Alumni" for a in annees(m)]
        self.assertEqual((min(alumni), max(alumni)), (1990, 2026))
        utilises = {g["groupe_uuid"] for m in self.membres for g in m["groupes"] if g["timeline"]}
        diplomes = {g["uuid"] for g in self.export["groupes"] if g["type"] == "diplome"}
        self.assertEqual(utilises, diplomes)

    def test_les_etudiants_sortiront_en_2027_ou_2028(self):
        etudiants = [a for m in self.membres if m["categorie"] == "Étudiant" for a in annees(m)]
        self.assertEqual(len(etudiants), 9)
        self.assertTrue(all(a in (2027, 2028) for a in etudiants))

    def test_plusieurs_diplomes_le_second_trois_ans_plus_tard(self):
        plusieurs = [m for m in self.membres if len(annees(m)) > 1]
        self.assertEqual(len(plusieurs), 120)
        self.assertTrue(all(second == premier + 3 for premier, second in map(annees, plusieurs)))

    # --- Les mots de passe --------------------------------------------------------------

    def test_le_hasher_de_django_donne_la_meme_empreinte_que_django(self):
        empreinte = PBKDF2PasswordHasher().encode("rapide-pour-test", "selCourt", 1000)
        self.assertEqual(empreinte, EMPREINTE_DJANGO)

    def test_mots_de_passe_relus_par_django(self):
        empreinte = self.membres[0]["password"]
        self.assertTrue(empreinte.startswith("pbkdf2_sha256$1000$"))
        self.assertTrue(check_password("motdepasse-factice", empreinte))
        self.assertFalse(check_password("autre-chose", empreinte))
