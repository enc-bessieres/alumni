from django.test import TestCase
from django.urls import reverse

from membres.models import Membre
from referentiels.models import Diplome, Formation, Site


class AccueilTests(TestCase):
    def test_la_page_d_accueil_s_affiche(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Alumni ENC Bessières")

    def test_la_page_d_accueil_charge_htmx(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertContains(reponse, "htmx-2.0.11.min.js")

    def test_sante_repond_ok(self):
        reponse = self.client.get(reverse("accueil:sante"))

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.content, b"ok")


def creer_membre(email, nom="Test", **champs):
    return Membre.objects.create_user(
        email, prenom="Test", nom=nom, categorie=Membre.Categorie.ADMINISTRATIF, **champs
    )


class ChiffresClesTests(TestCase):
    def chiffres(self):
        return self.client.get(reverse("accueil:index")).context["chiffres"]

    def test_seuls_les_membres_valides_sont_comptes(self):
        creer_membre("valide@exemple.test", statut_inscription=Membre.StatutInscription.VALIDEE)
        creer_membre("en-attente@exemple.test")
        creer_membre(
            "inactif@exemple.test",
            statut_inscription=Membre.StatutInscription.VALIDEE,
            is_active=False,
        )

        self.assertEqual(self.chiffres()["membres"], 1)

    def test_une_promo_n_est_comptee_qu_une_fois(self):
        diplome = Diplome.objects.first()
        site = Site.objects.first()
        for email, promo in [
            ("a@exemple.test", 2024),
            ("b@exemple.test", 2024),
            ("c@exemple.test", 2023),
        ]:
            Formation.objects.create(
                membre=creer_membre(email), diplome=diplome, site=site, promo=promo
            )

        self.assertEqual(self.chiffres()["promos"], 2)


class DerniersInscritsTests(TestCase):
    def setUp(self):
        valide = Membre.StatutInscription.VALIDEE
        creer_membre(
            "visible@exemple.test",
            nom="Visible",
            statut_inscription=valide,
            visible_dans_annuaire=True,
        )
        creer_membre(
            "cache@exemple.test",
            nom="Cache",
            statut_inscription=valide,
            visible_dans_annuaire=False,
        )
        creer_membre("attente@exemple.test", nom="Attente", visible_dans_annuaire=True)
        self.lecteur = creer_membre("lecteur@exemple.test", statut_inscription=valide)

    def test_un_visiteur_ne_voit_aucun_nom(self):
        reponse = self.client.get(reverse("accueil:index"))

        self.assertNotContains(reponse, "Derniers inscrits")
        self.assertNotContains(reponse, "Visible")
        self.assertContains(reponse, "Rejoindre le réseau")

    def test_un_membre_voit_seulement_les_membres_de_l_annuaire(self):
        self.client.force_login(self.lecteur)

        reponse = self.client.get(reverse("accueil:index"))

        self.assertContains(reponse, "Visible")
        self.assertNotContains(reponse, "Cache")
        self.assertNotContains(reponse, "Attente")
