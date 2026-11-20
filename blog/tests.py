from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article


class ArticlesPublicsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.publie = Article.objects.create(
            titre="Article publié",
            slug="publie",
            contenu="<p>Bonjour</p>",
            statut=Article.Statut.PUBLIE,
            publie_le=timezone.now(),
        )
        cls.brouillon = Article.objects.create(
            titre="Article en brouillon",
            slug="brouillon",
            contenu="<p>Pas encore prêt</p>",
        )

    def test_la_liste_montre_seulement_les_articles_publies(self):
        reponse = self.client.get(reverse("blog:liste"))
        self.assertContains(reponse, "Article publié")
        self.assertNotContains(reponse, "Article en brouillon")

    def test_un_article_publie_s_affiche(self):
        reponse = self.client.get(reverse("blog:detail", args=["publie"]))
        self.assertContains(reponse, "<p>Bonjour</p>")

    def test_un_brouillon_donne_une_404(self):
        reponse = self.client.get(reverse("blog:detail", args=["brouillon"]))
        self.assertEqual(reponse.status_code, 404)

    def test_la_liste_vide_affiche_un_message(self):
        Article.objects.all().delete()
        reponse = self.client.get(reverse("blog:liste"))
        self.assertContains(reponse, "Aucun article pour l'instant.")

    def test_le_contenu_d_un_article_est_nettoye(self):
        article = Article.objects.create(
            titre="Piège",
            slug="piege",
            contenu="<p>Texte</p><script>alert(1)</script>",
        )
        article.refresh_from_db()
        self.assertNotIn("<script", article.contenu)
