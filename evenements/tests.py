import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Evenement


class EvenementModelTests(TestCase):
    def test_creation_et_str_evenement(self):
        maintenant = timezone.now()
        organisateur = get_user_model().objects.create_user(
            email="organisateur@exemple.test",
            password="motdepasse-test-123",
        )
        identifiant_legacy = uuid.uuid4()
        evenement = Evenement.objects.create(
            titre="Soirée réseau Alumni",
            slug="soiree-reseau-alumni",
            description="<p>Rencontre annuelle des anciens élèves.</p>",
            date_debut=maintenant + timedelta(days=7),
            lieu="Paris",
            places=50,
            organisateur=organisateur,
            publie=True,
            legacy_id=identifiant_legacy,
        )
        self.assertEqual(str(evenement), "Soirée réseau Alumni")
        self.assertEqual(evenement.slug, "soiree-reseau-alumni")
        self.assertEqual(evenement.places, 50)
        self.assertEqual(evenement.organisateur, organisateur)
        self.assertEqual(evenement.legacy_id, identifiant_legacy)
        self.assertTrue(evenement.publie)
        self.assertIsNotNone(evenement.cree_le)

    def test_ordre_par_defaut_date_debut_decroissante(self):
        maintenant = timezone.now()
        ancien = Evenement.objects.create(
            titre="Événement passé",
            slug="evenement-passe",
            date_debut=maintenant - timedelta(days=5),
        )
        recent = Evenement.objects.create(
            titre="Événement à venir",
            slug="evenement-a-venir",
            date_debut=maintenant + timedelta(days=5),
        )
        self.assertEqual(list(Evenement.objects.all()), [recent, ancien])

    def test_date_fin_avant_date_debut_refusee(self):
        debut = timezone.now().replace(hour=16, minute=0, second=0, microsecond=0)
        fin = debut.replace(hour=12, minute=0)
        evenement = Evenement(
            titre="Atelier du matin",
            slug="atelier-du-matin",
            date_debut=debut,
            date_fin=fin,
        )
        with self.assertRaises(ValidationError):
            evenement.full_clean()


class EvenementDroitsTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.groupe_admin = Group.objects.get(name="Administrateur")
        self.url_ajout = reverse("admin:evenements_evenement_add")

    def test_membre_groupe_administrateur_peut_ajouter(self):
        admin_user = self.user_model.objects.create_user(
            email="admin_evenement@exemple.test",
            password="motdepasse-test-123",
            is_staff=True,
        )
        admin_user.groups.add(self.groupe_admin)
        self.client.force_login(admin_user)

        reponse = self.client.post(
            self.url_ajout,
            {
                "titre": "Forum des métiers",
                "slug": "forum-des-metiers",
                "description": "",
                "date_debut_0": "2026-12-10",
                "date_debut_1": "14:00:00",
                "date_fin_0": "2026-12-10",
                "date_fin_1": "17:00:00",
                "lieu": "ENC Bessières",
                "places": "100",
                "organisateur": "",
                "publie": "on",
            },
        )
        if reponse.status_code == 200:
            self.fail(f"Formulaire refusé : {reponse.context_data['adminform'].form.errors}")
        self.assertEqual(reponse.status_code, 302)
        self.assertEqual(Evenement.objects.count(), 1)

    def test_membre_sans_groupe_ne_peut_pas_ajouter(self):
        membre_simple = self.user_model.objects.create_user(
            email="membre_simple@exemple.test",
            password="motdepasse-test-123",
            is_staff=True,
        )
        self.client.force_login(membre_simple)

        reponse = self.client.post(
            self.url_ajout,
            {
                "titre": "Événement non autorisé",
                "slug": "evenement-non-autorise",
                "description": "",
                "date_debut_0": "2026-12-10",
                "date_debut_1": "14:00:00",
                "date_fin_0": "2026-12-10",
                "date_fin_1": "17:00:00",
                "lieu": "Paris",
            },
        )
        self.assertEqual(reponse.status_code, 403)
        self.assertEqual(Evenement.objects.count(), 0)
