from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Evenement


class EvenementModelTests(TestCase):
    def test_creation_et_str_evenement(self):
        maintenant = timezone.now()
        evenement = Evenement.objects.create(
            titre="Soirée réseau Alumni",
            description="<p>Rencontre annuelle des anciens élèves.</p>",
            date_debut=maintenant + timedelta(days=7),
            lieu="Paris",
            publie=True,
        )
        self.assertEqual(str(evenement), "Soirée réseau Alumni")
        self.assertTrue(evenement.publie)
        self.assertIsNotNone(evenement.cree_le)

    def test_ordre_par_defaut_date_debut_decroissante(self):
        maintenant = timezone.now()
        ancien = Evenement.objects.create(
            titre="Événement passé",
            date_debut=maintenant - timedelta(days=5),
        )
        recent = Evenement.objects.create(
            titre="Événement à venir",
            date_debut=maintenant + timedelta(days=5),
        )
        self.assertEqual(list(Evenement.objects.all()), [recent, ancien])
