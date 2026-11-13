"""Le générateur de faux membres, testé sans base de données."""

from collections import Counter

from django.test import SimpleTestCase

from membres.models import Membre
from referentiels.donnees import DIPLOMES, SITES

from .fausses_donnees import (
    NOMBRE_PAR_DEFAUT,
    REPARTITION,
    en_ascii,
    generer_membres,
    repartir,
)

TOUS_LES_DIPLOMES = {nom for noms in DIPLOMES.values() for nom in noms}


class GenererMembresTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.annuaire = generer_membres()  # les 1222 membres par défaut, calculés une fois

    def test_la_meme_graine_donne_les_memes_membres(self):
        self.assertEqual(generer_membres(50), generer_membres(50))
        self.assertNotEqual(generer_membres(50, graine=1), generer_membres(50))

    def test_genere_le_nombre_demande(self):
        self.assertEqual(len(generer_membres(7)), 7)
        self.assertEqual(generer_membres(0), [])
        self.assertEqual(len(self.annuaire), NOMBRE_PAR_DEFAUT)

    def test_par_defaut_la_repartition_est_celle_de_l_annuaire(self):
        # Issue #10 : Alumni 1143, Enseignant 50, Équipe administrative 10, Étudiant 9,
        # Candidat 9, Recruteur 1.
        self.assertEqual(Counter(m["categorie"] for m in self.annuaire), REPARTITION)

    def test_un_autre_nombre_garde_les_proportions(self):
        categories = Counter(repartir(100))
        self.assertEqual(sum(categories.values()), 100)
        # 100 × 1143 / 1222 = 93,5 : 93 alumni, et les places restantes vont aux petites
        # catégories, dont le reste après la virgule est plus grand (0,8 et 0,7).
        self.assertEqual(categories["alumni"], 93)
        self.assertLessEqual(set(categories), set(REPARTITION))

    def test_les_categories_existent_dans_le_modele_membre(self):
        self.assertLessEqual(set(REPARTITION), set(Membre.Categorie.values))

    def test_les_adresses_sont_uniques_et_de_test(self):
        adresses = [m["email"] for m in self.annuaire]
        self.assertEqual(len(set(adresses)), len(adresses))
        for adresse in adresses:
            self.assertRegex(adresse, r"^[a-z0-9]+\.[a-z0-9]+\.[0-9]+@exemple\.test$")

    def test_en_ascii_retire_accents_espaces_et_apostrophes(self):
        self.assertEqual(en_ascii("Lefèvre"), "lefevre")
        self.assertEqual(en_ascii("N'Diaye"), "ndiaye")
        self.assertEqual(en_ascii("Da Silva"), "dasilva")

    def test_seuls_les_alumni_et_les_etudiants_ont_un_parcours(self):
        for membre in self.annuaire:
            nombre = len(membre["parcours"])
            if membre["categorie"] == "alumni":
                self.assertIn(nombre, (1, 2))
            elif membre["categorie"] == "etudiant":
                self.assertEqual(nombre, 1)
            else:
                self.assertEqual(nombre, 0)
            for etape in membre["parcours"]:
                self.assertIn(etape["diplome"], TOUS_LES_DIPLOMES)
                self.assertIn(etape["site"], SITES)

    def test_environ_un_alumni_sur_cinq_a_deux_diplomes(self):
        alumni = [m for m in self.annuaire if m["categorie"] == "alumni"]
        avec_deux = sum(len(m["parcours"]) == 2 for m in alumni)
        self.assertTrue(0.15 < avec_deux / len(alumni) < 0.25, avec_deux)

    def test_promos_de_1990_a_2026_sur_les_20_diplomes(self):
        etapes = [e for m in self.annuaire if m["categorie"] == "alumni" for e in m["parcours"]]
        promos = [e["promo"] for e in etapes]
        self.assertEqual((min(promos), max(promos)), (1990, 2026))
        self.assertEqual({e["diplome"] for e in etapes}, TOUS_LES_DIPLOMES)

    def test_le_second_diplome_est_obtenu_apres_le_premier(self):
        for membre in self.annuaire:
            if len(membre["parcours"]) == 2:
                premier, second = (etape["promo"] for etape in membre["parcours"])
                self.assertTrue(1 <= second - premier <= 3)

    def test_un_etudiant_sortira_en_2027_ou_2028(self):
        for membre in self.annuaire:
            if membre["categorie"] == "etudiant":
                self.assertIn(membre["parcours"][0]["promo"], (2027, 2028))
