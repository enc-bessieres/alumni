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


class ValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        utilisateurs = get_user_model().objects
        mdp = "motdepasse-factice"
        identite = {"prenom": "Test", "nom": "Exemple"}
        cls.admin = utilisateurs.create_superuser("admin@exemple.test", mdp, **identite)
        cls.membre = utilisateurs.create_user("membre@exemple.test", mdp, **identite)
        cls.liste_admin = reverse("admin:blog_article_changelist")

    def creer_article(self):
        return Article.objects.create(
            titre="En attente",
            slug="en-attente",
            contenu="<p>Texte</p>",
            statut=Article.Statut.EN_ATTENTE,
        )

    def lancer_action(self, action, article):
        return self.client.post(
            self.liste_admin, {"action": action, "_selected_action": [article.pk]}
        )

    def test_publier_remplit_la_date_de_publication(self):
        article = self.creer_article()
        article.statut = Article.Statut.PUBLIE
        article.save()
        self.assertIsNotNone(article.publie_le)

    def test_l_equipe_publie_depuis_l_admin(self):
        article = self.creer_article()
        self.client.force_login(self.admin)
        self.lancer_action("publier", article)
        article.refresh_from_db()
        self.assertEqual(article.statut, Article.Statut.PUBLIE)
        self.assertIsNotNone(article.publie_le)

    def test_l_equipe_refuse_depuis_l_admin(self):
        article = self.creer_article()
        self.client.force_login(self.admin)
        self.lancer_action("refuser", article)
        article.refresh_from_db()
        self.assertEqual(article.statut, Article.Statut.REFUSE)

    def test_un_membre_hors_equipe_ne_peut_pas_valider(self):
        article = self.creer_article()
        self.client.force_login(self.membre)
        reponse = self.lancer_action("publier", article)
        self.assertEqual(reponse.status_code, 403)
        article.refresh_from_db()
        self.assertEqual(article.statut, Article.Statut.EN_ATTENTE)
