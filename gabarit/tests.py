import re

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.html import escape

from .menu import MENU, NB_ENTREES_MOBILE
from .urls import urlpatterns as pages_provisoires


class GabaritCommunTests(TestCase):
    def test_l_entete_affiche_le_nom_du_site_et_mene_a_l_accueil(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertContains(reponse, '<a class="marque" href="/">')
        self.assertContains(reponse, "Alumni ENC Bessières")

    def test_le_pied_de_page_cite_les_deux_sites(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertContains(reponse, "<footer")
        self.assertContains(reponse, "ENC Bessières Apprentissage")


class MenuTests(TestCase):
    def test_le_menu_affiche_tous_les_libelles(self):
        reponse = self.client.get(reverse("accueil:index"))

        for entree in MENU:
            self.assertContains(reponse, escape(entree.libelle))

    def test_la_barre_mobile_a_quatre_entrees_puis_plus(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertEqual(len(reponse.context["menu_mobile"]), NB_ENTREES_MOBILE)
        self.assertEqual(len(reponse.context["menu_plus"]), len(MENU) - NB_ENTREES_MOBILE)
        self.assertContains(reponse, "<summary>Plus</summary>")

    def test_l_entree_de_la_page_courante_est_active(self):
        reponse = self.client.get(reverse("gabarit:annuaire"))

        actives = [e["libelle"] for e in reponse.context["menu"] if e["actif"]]
        self.assertEqual(actives, ["Annuaire"])
        self.assertContains(reponse, 'aria-current="page"')

    def test_les_pages_provisoires_affichent_bientot_disponible(self):
        for page in pages_provisoires:
            with self.subTest(page=page.name):
                reponse = self.client.get(reverse(f"gabarit:{page.name}"))

                self.assertContains(reponse, "Bientôt disponible.")


class CouleursTests(SimpleTestCase):
    def lire_css(self):
        chemin = settings.BASE_DIR / "static" / "css" / "site.css"
        return chemin.read_text(encoding="utf-8")

    def test_le_bordeaux_est_declare_dans_root(self):
        racine = re.search(r":root\s*\{(.*?)\}", self.lire_css(), re.DOTALL).group(1)

        self.assertIn("--bordeaux:", racine)

    def test_les_couleurs_ne_sont_ecrites_que_dans_root(self):
        hors_racine = re.sub(r":root\s*\{.*?\}", "", self.lire_css(), count=1, flags=re.DOTALL)

        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b|rgb\(", hors_racine), [])
