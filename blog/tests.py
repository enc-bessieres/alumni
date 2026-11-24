from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from moderation.models import MotInterdit

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

    def test_un_article_en_attente_ou_refuse_donne_une_404(self):
        for statut in [Article.Statut.EN_ATTENTE, Article.Statut.REFUSE]:
            with self.subTest(statut=statut):
                Article.objects.create(
                    titre="Cache", slug=statut, contenu="<p>Cache</p>", statut=statut
                )
                reponse = self.client.get(reverse("blog:detail", args=[statut]))
                self.assertEqual(reponse.status_code, 404)


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

    def test_l_auteur_se_remplit_tout_seul_dans_l_admin(self):
        self.client.force_login(self.administrateur)
        self.client.post(
            reverse("admin:blog_article_add"),
            {
                "titre": "Par l'admin",
                "slug": "par-l-admin",
                "resume": "",
                "contenu": "<p>Texte</p>",
                "auteur": "",
                "statut": Article.Statut.BROUILLON,
                "publie_le_0": "",
                "publie_le_1": "",
            },
        )
        article = Article.objects.get(slug="par-l-admin")
        self.assertEqual(article.auteur, self.administrateur)

    def test_le_contenu_d_un_article_est_nettoye(self):
        article = Article.objects.create(
            titre="Piège",
            slug="piege",
            contenu="<p>Texte</p><script>alert(1)</script>",
        )
        article.refresh_from_db()
        self.assertNotIn("<script", article.contenu)

    def test_un_administrateur_retire_un_article(self):
        article = Article.objects.create(
            titre="A retirer",
            slug="a-retirer",
            contenu="<p>X</p>",
            statut=Article.Statut.PUBLIE,
        )
        self.client.force_login(self.administrateur)
        self.client.post(
            reverse("admin:blog_article_changelist"),
            {"action": "retirer", "_selected_action": [article.pk]},
        )
        article.refresh_from_db()
        self.assertEqual(article.statut, Article.Statut.REFUSE)
        self.assertTrue(
            LogEntry.objects.filter(object_id=str(article.pk), user=self.administrateur).exists()
        )


class EcrireUnArticleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Membre = get_user_model()
        cls.membre = Membre.objects.create_user(
            "membre@exemple.test",
            "motdepasse-factice",
            prenom="Test",
            nom="Exemple",
            statut_inscription=Membre.StatutInscription.VALIDEE,
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

    def test_un_membre_publie_un_article(self):
        self.client.force_login(self.membre)
        self.envoyer()
        article = Article.objects.get()
        self.assertEqual(article.statut, Article.Statut.PUBLIE)
        self.assertIsNotNone(article.publie_le)
        self.assertEqual(article.auteur, self.membre)
        self.assertEqual(article.slug, "mon-article")

    def test_un_article_envoye_est_visible_du_public(self):
        self.client.force_login(self.membre)
        self.envoyer()
        self.client.logout()
        reponse = self.client.get(reverse("blog:liste"))
        self.assertContains(reponse, "Mon article")

    def test_deux_titres_identiques_donnent_deux_adresses(self):
        self.client.force_login(self.membre)
        self.envoyer()
        self.envoyer()
        adresses = sorted(Article.objects.values_list("slug", flat=True))
        self.assertEqual(adresses, ["mon-article", "mon-article-2"])

    def test_un_membre_non_valide_ne_peut_pas_ecrire(self):
        non_valide = get_user_model().objects.create_user(
            "nonvalide@exemple.test", "motdepasse-factice", prenom="Test", nom="Exemple"
        )
        self.client.force_login(non_valide)
        reponse = self.envoyer()
        self.assertEqual(reponse.status_code, 403)
        self.assertFalse(Article.objects.exists())


class ListeNoireTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Membre = get_user_model()
        cls.membre = Membre.objects.create_user(
            "membre@exemple.test",
            "motdepasse-factice",
            prenom="Test",
            nom="Exemple",
            statut_inscription=Membre.StatutInscription.VALIDEE,
        )
        MotInterdit.objects.create(mot="motinterdit")

    def test_un_article_avec_un_mot_interdit_est_refuse(self):
        self.client.force_login(self.membre)
        reponse = self.client.post(
            reverse("blog:ecrire"),
            {"titre": "Titre", "resume": "", "contenu": "<p>Un motinterdit ici</p>"},
        )
        self.assertContains(reponse, "Votre article contient un mot interdit.")
        self.assertFalse(Article.objects.exists())


class SignalementAdminTest:
    def test_lien_vers_la_fiche_de_l_article(self):
        reponse = self.client.get(self.url)
        adresse = reverse("admin:blog_article_change", args=[self.tres_signale.pk])
        self.assertContains(reponse, f'href="{adresse}"')
