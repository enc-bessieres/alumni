from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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


class BackOfficeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrateur = get_user_model().objects.create_user(
            "administrateur@exemple.test",
            "motdepasse-factice",
            prenom="Test",
            nom="Exemple",
            is_staff=True,
        )
        cls.administrateur.groups.add(Group.objects.get(name="Administrateur"))

    def test_un_administrateur_voit_les_articles(self):
        self.client.force_login(self.administrateur)
        reponse = self.client.get(reverse("admin:blog_article_changelist"))
        self.assertEqual(reponse.status_code, 200)

    def test_publier_remplit_la_date_de_publication(self):
        article = Article.objects.create(
            titre="X", slug="x", contenu="<p>X</p>", statut=Article.Statut.PUBLIE
        )
        self.assertIsNotNone(article.publie_le)
