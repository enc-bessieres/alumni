from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import Page

PAGES_DE_DEPART = ["a-propos", "mentions-legales", "cgu", "confidentialite", "charte-du-mentorat"]


class PagesLibresTests(TestCase):
    def test_l_adresse_d_une_page(self):
        self.assertEqual(reverse("pages_libres:detail", args=["a-propos"]), "/page/a-propos/")

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

    def test_les_pages_de_depart_existent(self):
        for slug in PAGES_DE_DEPART:
            with self.subTest(slug=slug):
                self.assertEqual(Page.objects.get(slug=slug).contenu, "À COMPLÉTER par l'ENC")
                reponse = self.client.get(reverse("pages_libres:detail", args=[slug]))
                self.assertEqual(reponse.status_code, 200)


class BackOfficeTests(TestCase):
    """Back-office réservé à l'équipe ; un non-administrateur connecté reçoit une 403."""

    @classmethod
    def setUpTestData(cls):
        utilisateurs = get_user_model().objects
        mdp = "motdepasse-factice"
        cls.admin = utilisateurs.create_superuser("admin", "admin@exemple.test", mdp)
        cls.equipe = utilisateurs.create_user("equipe", "equipe@exemple.test", mdp, is_staff=True)
        cls.membre = utilisateurs.create_user("membre", "membre@exemple.test", mdp)
        cls.liste = reverse("admin:pages_libres_page_changelist")

    def test_l_administrateur_voit_les_pages(self):
        self.client.force_login(self.admin)

        reponse = self.client.get(self.liste)

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Mentions légales")

    def test_l_administrateur_modifie_une_page(self):
        page = Page.objects.get(slug="cgu")
        self.client.force_login(self.admin)

        self.client.post(
            reverse("admin:pages_libres_page_change", args=[page.pk]),
            {"titre": page.titre, "slug": "cgu", "contenu": "Nouveau texte", "publiee": "on"},
        )

        page.refresh_from_db()
        self.assertEqual(page.contenu, "Nouveau texte")

    def test_un_non_administrateur_recoit_une_403(self):
        self.client.force_login(self.membre)

        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 403)
        self.assertEqual(self.client.get(self.liste).status_code, 403)

    def test_un_visiteur_non_connecte_est_renvoye_a_la_connexion(self):
        reponse = self.client.get(self.liste)

        self.assertRedirects(reponse, f"{reverse('admin:login')}?next={self.liste}")

    def test_l_equipe_sans_permission_ne_peut_rien_modifier(self):
        self.client.force_login(self.equipe)

        self.assertEqual(self.client.get(self.liste).status_code, 403)
        ajout = reverse("admin:pages_libres_page_add")
        reponse = self.client.post(ajout, {"titre": "Pirate", "slug": "pirate", "contenu": "x"})
        self.assertEqual(reponse.status_code, 403)
        self.assertFalse(Page.objects.filter(slug="pirate").exists())

    def test_l_equipe_avec_la_permission_peut_modifier(self):
        self.equipe.user_permissions.add(Permission.objects.get(codename="change_page"))
        self.client.force_login(self.equipe)

        self.assertEqual(self.client.get(self.liste).status_code, 200)
