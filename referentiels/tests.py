"""
Référentiels : sites, niveaux, diplômes, et le parcours des membres (issue #10).
La base de test est créée avec toutes les migrations, donc avec les données de la 0002.
"""

import uuid

from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre

from .creation import creer_referentiels
from .donnees import DIPLOMES, SECTEURS, TYPES_DE_CONTRAT
from .models import Diplome, Formation, Niveau, Secteur, Site, Tag, TypeDeContrat

TOUS_LES_DIPLOMES = [nom for noms in DIPLOMES.values() for nom in noms]
MOT_DE_PASSE = "motdepasse-de-test"


class DonneesInitialesTests(TestCase):
    """Ce que la migration 0002 a mis dans la base."""

    def test_la_migration_cree_2_sites_2_niveaux_et_20_diplomes(self):
        self.assertEqual(
            sorted(Site.objects.values_list("nom", flat=True)),
            ["ENC Bessières", "ENC Bessières Apprentissage"],
        )
        self.assertEqual(sorted(Niveau.objects.values_list("nom", flat=True)), ["BTS", "Prépa"])
        self.assertEqual(len(TOUS_LES_DIPLOMES), 20)
        self.assertEqual(
            sorted(Diplome.objects.values_list("nom", flat=True)), sorted(TOUS_LES_DIPLOMES)
        )

    def test_chaque_diplome_est_rattache_a_son_niveau(self):
        self.assertEqual(Diplome.objects.get(nom="BTS SIO").niveau.nom, "BTS")
        self.assertEqual(Diplome.objects.get(nom="DCG").niveau.nom, "Prépa")
        self.assertEqual(Niveau.objects.get(nom="BTS").diplomes.count(), 11)

    def test_relancer_la_creation_ne_cree_pas_de_doublon(self):
        creer_referentiels(Site, Niveau, Diplome)
        creer_referentiels(Site, Niveau, Diplome)
        self.assertEqual(Diplome.objects.count(), 20)
        self.assertEqual(Site.objects.count(), 2)


class ReglesTests(TestCase):
    """Ce que la base refuse."""

    def test_deux_diplomes_ne_peuvent_pas_porter_le_meme_nom(self):
        with self.assertRaises(IntegrityError):
            Diplome.objects.create(nom="BTS SIO", niveau=Niveau.objects.get(nom="BTS"))

    def test_on_ne_supprime_pas_un_niveau_qui_a_des_diplomes(self):
        with self.assertRaises(ProtectedError):
            Niveau.objects.get(nom="BTS").delete()

    def test_plusieurs_elements_peuvent_ne_pas_avoir_d_identifiant_datalumni(self):
        # Ce qui est créé sur le nouveau site n'a pas de legacy_id : NULL n'est pas un doublon.
        Site.objects.create(nom="Site sans legacy_id 1")
        Site.objects.create(nom="Site sans legacy_id 2")
        self.assertEqual(Site.objects.filter(legacy_id__isnull=True).count(), 4)


class BackOfficeTests(TestCase):
    """Les droits du back-office sont ceux de Django : statut « équipe » + permissions."""

    @classmethod
    def setUpTestData(cls):
        # Le compte de connexion est le Membre : on se connecte avec son e-mail, sans
        # identifiant, et le prénom et le nom sont obligatoires.
        identite = {"prenom": "Test", "nom": "Exemple"}
        cls.admin = Membre.objects.create_superuser("admin@exemple.test", MOT_DE_PASSE, **identite)
        cls.equipe = Membre.objects.create_user(
            "equipe@exemple.test", MOT_DE_PASSE, is_staff=True, **identite
        )
        cls.membre = Membre.objects.create_user("membre@exemple.test", MOT_DE_PASSE, **identite)
        cls.liste = reverse("admin:referentiels_diplome_changelist")

    def test_l_administrateur_voit_les_20_diplomes(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(self.liste)
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "20 diplômes")

    def test_un_membre_ordinaire_n_entre_pas_dans_le_back_office(self):
        self.client.force_login(self.membre)
        reponse = self.client.get(self.liste)
        # Django le renvoie vers la connexion (302) ; avec le back-office de #23 (pages libres),
        # il reçoit une 403. Dans les deux cas, ce qui compte : il ne voit pas la liste.
        self.assertIn(reponse.status_code, (302, 403))
        self.assertNotContains(reponse, "20 diplômes", status_code=reponse.status_code)

    def test_l_equipe_sans_permission_ne_peut_rien_faire(self):
        self.client.force_login(self.equipe)
        self.assertEqual(self.client.get(self.liste).status_code, 403)
        ajout = reverse("admin:referentiels_diplome_add")
        self.assertEqual(self.client.post(ajout, {"nom": "Pirate"}).status_code, 403)
        self.assertFalse(Diplome.objects.filter(nom="Pirate").exists())

    def test_l_equipe_avec_la_permission_peut_consulter(self):
        self.equipe.user_permissions.add(Permission.objects.get(codename="view_diplome"))
        self.client.force_login(self.equipe)
        self.assertEqual(self.client.get(self.liste).status_code, 200)

    def test_l_identifiant_datalumni_est_affiche_mais_pas_modifiable(self):
        sio = Diplome.objects.get(nom="BTS SIO")
        sio.legacy_id = uuid.UUID("00000000-0000-4000-8000-000000000001")
        sio.save()
        self.client.force_login(self.admin)
        reponse = self.client.get(reverse("admin:referentiels_diplome_change", args=[sio.pk]))
        self.assertContains(reponse, "00000000-0000-4000-8000-000000000001")
        self.assertNotContains(reponse, 'name="legacy_id"')  # aucun champ de saisie


class FormationTests(TestCase):
    """Le parcours d'un membre : diplôme + site + promo."""

    @classmethod
    def setUpTestData(cls):
        cls.membre = Membre.objects.create_user(
            "ines@exemple.test", MOT_DE_PASSE, prenom="Inès", nom="Exemple"
        )
        cls.sio = Diplome.objects.get(nom="BTS SIO")
        cls.dcg = Diplome.objects.get(nom="DCG")
        cls.site = Site.objects.get(nom="ENC Bessières")

    def formation(self, diplome, promo=2024):
        return Formation(membre=self.membre, diplome=diplome, site=self.site, promo=promo)

    def test_un_membre_peut_avoir_plusieurs_diplomes_donc_plusieurs_promos(self):
        self.formation(self.sio, 2022).save()
        self.formation(self.dcg, 2025).save()
        promos = list(self.membre.formations.values_list("diplome__nom", "promo"))
        self.assertEqual(promos, [("DCG", 2025), ("BTS SIO", 2022)])  # la plus récente d'abord

    def test_un_meme_diplome_ne_compte_qu_une_fois_par_membre(self):
        self.formation(self.sio, 2022).save()
        with self.assertRaises(IntegrityError):
            self.formation(self.sio, 2023).save()

    def test_la_promo_doit_etre_une_annee_plausible(self):
        with self.assertRaises(ValidationError):
            self.formation(self.sio, promo=24).full_clean()
        self.formation(self.sio, promo=2024).full_clean()  # pas d'erreur

    def test_supprimer_le_membre_supprime_son_parcours(self):
        self.formation(self.sio).save()
        self.membre.delete()
        self.assertEqual(Formation.objects.count(), 0)

    def test_on_ne_peut_pas_supprimer_un_diplome_suivi_par_un_membre(self):
        self.formation(self.sio).save()
        with self.assertRaises(ProtectedError):
            self.sio.delete()


class ReferentielsAdministrationTests(TestCase):
    """Types de contrat, secteurs et tags (#39) : listes de départ et back-office."""

    LISTES = ["typedecontrat", "secteur", "tag"]

    @classmethod
    def setUpTestData(cls):
        identite = {"prenom": "Test", "nom": "Exemple"}
        cls.administrateur = Membre.objects.create_user(
            "administrateur@exemple.test", MOT_DE_PASSE, is_staff=True, **identite
        )
        cls.administrateur.groups.add(Group.objects.get(name="Administrateur"))
        cls.equipe = Membre.objects.create_user(
            "equipe@exemple.test", MOT_DE_PASSE, is_staff=True, **identite
        )

    def test_la_migration_cree_les_types_de_contrat_et_les_secteurs(self):
        noms = TypeDeContrat.objects.values_list("nom", flat=True)
        self.assertEqual(sorted(noms), sorted(TYPES_DE_CONTRAT))
        self.assertEqual(sorted(Secteur.objects.values_list("nom", flat=True)), sorted(SECTEURS))
        self.assertEqual(Tag.objects.count(), 0)  # les tags se créent dans le back-office

    def test_un_type_de_contrat_ne_peut_pas_exister_deux_fois(self):
        with self.assertRaises(IntegrityError):
            TypeDeContrat.objects.create(nom="CDI")

    def test_l_administrateur_gere_les_trois_listes(self):
        self.client.force_login(self.administrateur)
        for liste in self.LISTES:
            with self.subTest(liste=liste):
                page = reverse(f"admin:referentiels_{liste}_changelist")
                self.assertEqual(self.client.get(page).status_code, 200)
        ajout = reverse("admin:referentiels_tag_add")
        self.client.post(ajout, {"nom": "Entrepreneuriat"})
        self.assertTrue(Tag.objects.filter(nom="Entrepreneuriat").exists())

    def test_l_equipe_sans_groupe_n_y_a_pas_acces(self):
        self.client.force_login(self.equipe)
        for liste in self.LISTES:
            with self.subTest(liste=liste):
                page = reverse(f"admin:referentiels_{liste}_changelist")
                self.assertEqual(self.client.get(page).status_code, 403)
