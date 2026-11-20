from django.contrib.auth import get_user_model
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


class EcrireUnArticleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.membre = get_user_model().objects.create_user(
            "membre@exemple.test", "motdepasse-factice", prenom="Test", nom="Exemple"
        )
        cls.adresse = reverse("blog:ecrire")

    def envoyer(self, **donnees):
        valeurs = {"titre": "Mon article", "resume": "", "contenu": "<p>Bonjour</p>"}
        valeurs.update(donnees)
        return self.client.post(self.adresse, valeurs)

    def test_un_visiteur_est_renvoye_vers_la_connexion(self):
        reponse = self.client.get(self.adresse)
        self.assertEqual(reponse.status_code, 302)
        self.assertIn("next=/blog/ecrire/", reponse.url)

    def test_un_membre_envoie_un_article_en_attente(self):
        self.client.force_login(self.membre)
        self.envoyer()
        article = Article.objects.get()
        self.assertEqual(article.statut, Article.Statut.EN_ATTENTE)
        self.assertEqual(article.auteur, self.membre)
        self.assertEqual(article.slug, "mon-article")

    def test_un_article_envoye_n_est_pas_visible_du_public(self):
        self.client.force_login(self.membre)
        self.envoyer()
        reponse = self.client.get(reverse("blog:liste"))
        self.assertNotContains(reponse, "Mon article")

    def test_deux_titres_identiques_donnent_deux_adresses(self):
        self.client.force_login(self.membre)
        self.envoyer()
        self.envoyer()
        adresses = sorted(Article.objects.values_list("slug", flat=True))
        self.assertEqual(adresses, ["mon-article", "mon-article-2"])

    def test_un_membre_ne_peut_pas_publier_lui_meme(self):
        self.client.force_login(self.membre)
        self.envoyer(statut="publie")
        self.assertEqual(Article.objects.get().statut, Article.Statut.EN_ATTENTE)
