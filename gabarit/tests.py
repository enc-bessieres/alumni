import re

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.html import escape
from django.views.defaults import permission_denied

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

    def test_seules_les_listes_des_menus_perdent_leurs_puces(self):
        css = (settings.BASE_DIR / "static" / "css" / "site.css").read_text(encoding="utf-8")

        # Aucune règle ne vise toutes les listes du site : celles du contenu gardent leurs puces.
        self.assertNotRegex(css, r"(?m)^ul\s*[,{]")
        self.assertIn("nav ul {", css)

    def test_les_pages_provisoires_affichent_bientot_disponible(self):
        for page in pages_provisoires:
            with self.subTest(page=page.name):
                reponse = self.client.get(reverse(f"gabarit:{page.name}"))

                self.assertContains(reponse, "Bientôt disponible.")


class FauxMembre:
    """Un membre connecté, sans base de données.

    La zone membre n'utilise que les méthodes standard d'un compte Django : elle fonctionne
    avec le modèle Membre d'Alex (issue #9) comme avec le compte par défaut.
    """

    is_authenticated = True

    def __init__(self, prenom, nom, email):
        self.prenom = prenom
        self.nom = nom
        self.email = email

    def get_short_name(self):
        return self.prenom

    def get_full_name(self):
        return f"{self.prenom} {self.nom}".strip()

    def get_username(self):
        return self.email


class ZoneMembreTests(SimpleTestCase):
    def afficher(self, utilisateur):
        requete = RequestFactory().get("/")
        requete.user = utilisateur
        return render_to_string("gabarit/zone_membre.html", request=requete)

    def test_un_visiteur_voit_se_connecter(self):
        html = self.afficher(AnonymousUser())

        self.assertIn("Se connecter", html)
        self.assertNotIn("Paramètres", html)

    def test_un_membre_voit_son_prenom_ses_initiales_et_son_menu(self):
        html = self.afficher(FauxMembre("Chloé", "Petit", "chloe.petit@exemple.test"))

        self.assertIn("Chloé", html)
        self.assertIn(">CP<", html)
        self.assertIn("Profil", html)
        self.assertIn("Paramètres", html)
        self.assertNotIn("Se connecter", html)

    def test_sans_nom_l_initiale_vient_de_l_identifiant(self):
        html = self.afficher(FauxMembre("", "", "bruno@exemple.test"))

        self.assertIn(">B<", html)
        self.assertIn("bruno@exemple.test", html)


class CouleursTests(SimpleTestCase):
    def lire_css(self):
        chemin = settings.BASE_DIR / "static" / "css" / "site.css"
        return chemin.read_text(encoding="utf-8")

    def test_le_bordeaux_est_declare_dans_root(self):
        racine = re.search(r":root\s*\{(.*?)\}", self.lire_css(), re.DOTALL).group(1)

        self.assertIn("--bordeaux:", racine)

    def test_les_couleurs_ne_sont_ecrites_que_dans_root(self):
        hors_racine = re.sub(r":root\s*\{.*?\}", "", self.lire_css(), count=1, flags=re.DOTALL)

        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", hors_racine), [])


class PagesErreurTests(TestCase):
    def test_la_page_404_utilise_le_gabarit(self):
        reponse = self.client.get("/cette-page-n-existe-pas/")

        self.assertContains(reponse, "Page introuvable", status_code=404)
        self.assertContains(reponse, "Annuaire", status_code=404)

    def test_la_page_403_utilise_le_gabarit(self):
        requete = RequestFactory().get("/page-interdite/")

        reponse = permission_denied(requete, PermissionDenied())

        self.assertContains(reponse, "Accès refusé", status_code=403)
        self.assertContains(reponse, "Annuaire", status_code=403)
