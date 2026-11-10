from django.test import TestCase
from django.urls import reverse


class AccueilTests(TestCase):
    def test_la_page_d_accueil_s_affiche(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Alumni ENC Bessières")

    def test_la_page_d_accueil_charge_htmx(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertContains(reponse, "htmx-2.0.11.min.js")

    def test_sante_repond_ok(self):
        reponse = self.client.get(reverse("accueil:sante"))

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.content, b"ok")
