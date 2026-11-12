from django.test import TestCase
from django.urls import reverse

from .models import Page


class PagesLibresTests(TestCase):
    def test_une_page_publiee_s_affiche(self):
        Page.objects.create(titre="Essai", slug="essai", contenu="Bonjour", publiee=True)

        reponse = self.client.get(reverse("pages_libres:detail", args=["essai"]))

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Bonjour")

    def test_une_page_non_publiee_donne_une_404(self):
        Page.objects.create(titre="Brouillon", slug="brouillon", contenu="x", publiee=False)

        reponse = self.client.get(reverse("pages_libres:detail", args=["brouillon"]))

        self.assertEqual(reponse.status_code, 404)

    def test_une_page_inconnue_donne_une_404(self):
        reponse = self.client.get(reverse("pages_libres:detail", args=["nexiste-pas"]))

        self.assertEqual(reponse.status_code, 404)

    def test_le_html_saisi_est_echappe(self):
        Page.objects.create(titre="X", slug="x", contenu="<script>alert(1)</script>", publiee=True)

        reponse = self.client.get(reverse("pages_libres:detail", args=["x"]))

        self.assertNotContains(reponse, "<script>alert(1)</script>")

    def test_les_pages_legales_existent_au_depart(self):
        for slug in ["a-propos", "mentions-legales", "cgu", "confidentialite"]:
            reponse = self.client.get(reverse("pages_libres:detail", args=[slug]))
            self.assertContains(reponse, "À COMPLÉTER")
