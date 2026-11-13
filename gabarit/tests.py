import json
import re
import struct

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.cookie import CookieStorage
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import include, path, reverse
from django.utils.html import escape
from django.views.defaults import permission_denied

from config.urls import urlpatterns as adresses_du_site

from .menu import MENU, NB_ENTREES_MOBILE, PIED_DE_PAGE
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


class ApplicationInstallableTests(TestCase):
    statique = settings.BASE_DIR / "static"

    def lire_manifeste(self):
        return json.loads((self.statique / "manifest.webmanifest").read_text(encoding="utf-8"))

    def bordeaux_du_css(self):
        css = (self.statique / "css" / "site.css").read_text(encoding="utf-8")
        return re.search(r"--bordeaux:\s*(#[0-9a-fA-F]{6})", css).group(1).lower()

    def dimensions_png(self, chemin):
        """Lit la largeur et la hauteur dans l'en-tête du fichier PNG."""
        entete = chemin.read_bytes()[:24]
        self.assertEqual(entete[:8], b"\x89PNG\r\n\x1a\n", f"{chemin.name} n'est pas un PNG")
        return struct.unpack(">II", entete[16:24])

    def test_le_manifeste_decrit_une_application_installable(self):
        manifeste = self.lire_manifeste()

        self.assertEqual(manifeste["name"], "Alumni ENC Bessières")
        self.assertEqual(manifeste["start_url"], "/")
        self.assertEqual(manifeste["display"], "standalone")

    def test_les_icones_du_manifeste_existent_a_la_bonne_taille(self):
        tailles = set()
        for icone in self.lire_manifeste()["icons"]:
            with self.subTest(icone=icone["src"]):
                largeur, hauteur = self.dimensions_png(self.statique / icone["src"])

                self.assertEqual(f"{largeur}x{hauteur}", icone["sizes"])
                tailles.add(icone["sizes"])

        # Android exige au moins une icône 192 et une 512.
        self.assertTrue({"192x192", "512x512"} <= tailles)

    def test_l_icone_iphone_fait_180_pixels(self):
        icone = self.statique / "icones" / "apple-touch-icon.png"

        self.assertEqual(self.dimensions_png(icone), (180, 180))

    def test_la_couleur_du_theme_est_le_bordeaux_du_css(self):
        bordeaux = self.bordeaux_du_css()
        reponse = self.client.get(reverse("accueil:index"))

        self.assertEqual(self.lire_manifeste()["theme_color"].lower(), bordeaux)
        self.assertContains(reponse, f'<meta name="theme-color" content="{bordeaux}">')

    def test_le_gabarit_annonce_le_manifeste_et_l_icone_iphone(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertContains(reponse, 'rel="manifest"')
        self.assertContains(reponse, "manifest.webmanifest")
        self.assertContains(reponse, 'rel="apple-touch-icon"')


class MessagesTests(SimpleTestCase):
    def afficher_la_page(self, *textes):
        requete = RequestFactory().get("/")
        requete.user = AnonymousUser()
        # Le stockage des messages, que le middleware de Django installe sur chaque requête.
        requete._messages = CookieStorage(requete)
        for texte in textes:
            messages.success(requete, texte)
        return render_to_string("base.html", request=requete)

    def test_les_messages_s_affichent_dans_le_gabarit(self):
        html = self.afficher_la_page("Vous êtes déconnecté.")

        self.assertIn('<ul class="messages" role="status">', html)
        self.assertIn("<li>Vous êtes déconnecté.</li>", html)

    def test_sans_message_rien_ne_s_affiche(self):
        html = self.afficher_la_page()

        self.assertNotIn('class="messages"', html)


def page_libre_factice(request, slug):
    """Remplace la vue des pages libres de Marie-Dominique (issue #12) le temps d'un test."""
    return HttpResponse(slug)


class AdressesSansPagesLibres:
    """Les vraies adresses du site, moins celles de l'application « pages_libres ».

    Partir des vraies adresses garde celles des autres applications, par exemple la connexion
    d'Alex (/compte/) : sans elle, la zone membre ne trouverait pas l'adresse de connexion.
    """

    urlpatterns = [
        adresse
        for adresse in adresses_du_site
        if getattr(adresse, "namespace", None) != "pages_libres"
    ]


class AdressesAvecPagesLibres:
    """Les mêmes, plus une application « pages_libres » factice, à la même adresse que la vraie."""

    pages_libres = [path("<slug:slug>/", page_libre_factice, name="detail")]
    urlpatterns = AdressesSansPagesLibres.urlpatterns + [
        path("page/", include((pages_libres, "pages_libres"))),
    ]


class PiedDePageTests(TestCase):
    @override_settings(ROOT_URLCONF=AdressesSansPagesLibres)
    def test_sans_les_pages_libres_le_pied_de_page_reste_a_completer(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertContains(reponse, "À COMPLÉTER : liens vers les mentions légales")
        self.assertNotContains(reponse, "liens-du-pied")

    @override_settings(ROOT_URLCONF=AdressesAvecPagesLibres)
    def test_avec_les_pages_libres_le_pied_de_page_affiche_leurs_liens(self):
        reponse = self.client.get(reverse("accueil:index"))

        for lien in PIED_DE_PAGE:
            with self.subTest(page=lien.slug):
                self.assertContains(reponse, f'<a href="/page/{lien.slug}/">{lien.libelle}</a>')
        self.assertNotContains(reponse, "À COMPLÉTER : liens vers les mentions légales")
