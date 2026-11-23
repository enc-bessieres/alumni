from django.test import TestCase

from .filtres import mots_trouves
from .models import MotInterdit


class ListeNoireTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        MotInterdit.objects.create(mot="motinterdit")

    def test_un_mot_interdit_est_trouve_malgre_majuscules_et_accents(self):
        self.assertIn("motinterdit", mots_trouves("<p>Un MOTÌNTERDIT ici</p>"))

    def test_un_mot_innocent_qui_le_contient_n_est_pas_bloque(self):
        self.assertNotIn("motinterdit", mots_trouves("<p>Des supermotinterdits</p>"))

    def test_un_mot_est_enregistre_en_minuscules(self):
        mot = MotInterdit.objects.create(mot="  AutreMot ")
        self.assertEqual(mot.mot, "autremot")
