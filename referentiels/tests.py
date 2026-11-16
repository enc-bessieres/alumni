"""
Référentiels : sites, niveaux, diplômes (issue #10).
La base de test est créée avec toutes les migrations, donc avec les données de la 0002.
"""

import uuid

from django.contrib.auth.models import Permission
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre

from .creation import creer_referentiels
from .donnees import DIPLOMES
from .models import Diplome, Niveau, Site

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
