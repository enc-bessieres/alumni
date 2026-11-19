"""
Export factice au format Datalumni (docs/migration/export-factice.md).
Ces tests n'ont pas besoin de la base de données.
"""

import json
from collections import defaultdict
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


def sans_mot_de_passe(m):
    return m["password"].startswith("!")


def nom(m):
    return f"{m['metadata']['prenom']} {m['metadata']['nom']}"


def diplomes(m):
    """Les diplômes et promos d'un membre, sous une forme comparable."""
    return sorted(
        f"{g['groupe_uuid']}/{g['timeline']['annee']}" for g in m["groupes"] if g["timeline"]
    )


class ExportFacticeTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.export = generer_export_factice()  # une seule fois : il faut environ une seconde
        cls.membres = cls.export["membres"]

    def compter(self, condition):
        return sum(1 for m in self.membres if condition(m))

    def regrouper(self, cle):
        """Range les membres par clé et garde les groupes de plus d'un membre."""
        groupes = defaultdict(list)
        for m in self.membres:
            groupes[cle(m)].append(m)
        return [g for g in groupes.values() if len(g) > 1]

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
        adresses = [m["email"] for m in self.membres if m["email"]]  # 5 membres n'en ont pas
        self.assertTrue(all(a.endswith(".test") for a in adresses))  # règle 1 : personne de réel
        self.assertEqual(len(set(adresses)), len(adresses))

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
        # 120 au départ ; les doublons recopient les diplômes, les homonymes en changent.
        self.assertGreaterEqual(len(plusieurs), 100)
        self.assertTrue(all(second == premier + 3 for premier, second in map(annees, plusieurs)))

    # --- Les profils et les mots de passe -----------------------------------------------

    def test_imite_les_profils_peu_remplis_de_la_plateforme_actuelle(self):
        # Issue #10 : 24 % de photos, 28 % d'expériences, 53 % de villes avec coordonnées.
        self.assertEqual(self.compter(lambda m: m["metadata"]["photo"]), round(1300 * 0.24))
        self.assertEqual(self.compter(lambda m: m["experiences"]), round(1300 * 0.28))
        lieux = [m["metadata"]["localisation"] for m in self.membres]
        lieux = [lieu for lieu in lieux if lieu]
        self.assertEqual(len(lieux), round(1300 * 0.53))
        self.assertTrue(all(isinstance(lieu["lat"], float) for lieu in lieux))
        photos = [m["metadata"]["photo"] for m in self.membres if m["metadata"]["photo"]]
        self.assertTrue(all(".exemple.test/" in p for p in photos))  # aucune vraie adresse

    def test_le_hasher_de_django_donne_la_meme_empreinte_que_django(self):
        empreinte = PBKDF2PasswordHasher().encode("rapide-pour-test", "selCourt", 1000)
        self.assertEqual(empreinte, EMPREINTE_DJANGO)

    def test_mots_de_passe_relus_par_django(self):
        empreinte = next(m["password"] for m in self.membres if not sans_mot_de_passe(m))
        self.assertTrue(empreinte.startswith("pbkdf2_sha256$1000$"))
        self.assertTrue(check_password("motdepasse-factice", empreinte))
        self.assertFalse(check_password("autre-chose", empreinte))

    # --- Les cas difficiles (docs/06-points-durs.md, § 1) -------------------------------

    def test_450_importes_jamais_actives_dont_40_emails_morts_et_5_sans_email(self):
        inactifs = [m for m in self.membres if sans_mot_de_passe(m) and not m["liaisons"]]
        self.assertEqual(len(inactifs), 450)
        self.assertTrue(all(m["origine"] == "import" for m in inactifs))
        self.assertTrue(all(m["derniere_connexion"] is None for m in inactifs))
        self.assertEqual(sum(1 for m in inactifs if m["email"].endswith("@mort.exemple.test")), 40)
        self.assertEqual(sum(1 for m in inactifs if m["email"] == ""), 5)

    def test_comptes_google_et_linkedin(self):
        def seulement(fournisseur):
            return self.compter(
                lambda m: (
                    sans_mot_de_passe(m)
                    and [liaison["fournisseur"] for liaison in m["liaisons"]] == [fournisseur]
                )
            )

        self.assertEqual(seulement("google"), 30)
        self.assertEqual(seulement("linkedin"), 10)
        self.assertEqual(self.compter(lambda m: not sans_mot_de_passe(m) and m["liaisons"]), 60)

    def test_25_doublons_meme_nom_memes_diplomes_un_importe_un_inscrit(self):
        paires = self.regrouper(lambda m: (nom(m), *diplomes(m)))
        self.assertEqual(len(paires), 25)
        for a, b in paires:
            self.assertNotEqual(a["email"], b["email"])
            self.assertEqual(sorted([a["origine"], b["origine"]]), ["import", "inscription"])

    def test_5_homonymes_qui_ne_sont_pas_des_doublons(self):
        meme_nom = self.regrouper(nom)
        # Seuls les doublons et les homonymes voulus portent le même nom, jamais par hasard.
        self.assertEqual(len(meme_nom), 25 + 5)
        self.assertEqual(sum(1 for a, b in meme_nom if diplomes(a) != diplomes(b)), 5)

    def test_inscriptions_en_attente_et_refusees_absentes_de_l_annuaire(self):
        def masques(statut):
            return self.compter(lambda m: m["statut"] == statut and not m["visible_annuaire"])

        self.assertEqual(masques("en_attente"), 10)
        self.assertEqual(masques("refuse"), 5)
        self.assertEqual(self.compter(lambda m: m["statut"] != "accepte"), 15)
