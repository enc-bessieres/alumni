"""
Connexion par e-mail et mot de passe, avec django-allauth.
Mots de passe et adresses inventés (règle 1).
"""

from allauth.account.models import EmailAddress
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.test import TestCase

from membres.models import Membre

MOT_DE_PASSE = "motdepasse-de-test"


def creer_membre(email, adresse_verifiee=True, **champs):
    """Un membre avec son adresse, vérifiée comme le seront celles importées de Datalumni."""
    champs.setdefault("categorie", Membre.Categorie.ALUMNI)
    champs.setdefault("statut_inscription", Membre.StatutInscription.VALIDEE)
    membre = Membre.objects.create_user(email, MOT_DE_PASSE, prenom="Test", nom="Test", **champs)
    EmailAddress.objects.create(user=membre, email=email, verified=adresse_verifiee, primary=True)
    return membre


def se_connecter(client, email, mot_de_passe=MOT_DE_PASSE):
    return client.post("/compte/login/", {"login": email, "password": mot_de_passe})


class ConnexionTests(TestCase):
    def test_la_page_de_connexion_est_accessible_sans_etre_connecte(self):
        self.assertContains(self.client.get("/compte/login/"), "Connexion")

    def test_un_membre_se_connecte_avec_son_e_mail(self):
        creer_membre("ines@exemple.test")
        reponse = se_connecter(self.client, "ines@exemple.test")
        self.assertRedirects(reponse, "/")
        self.assertEqual(self.client.get("/").context["user"].email, "ines@exemple.test")

    def test_un_mauvais_mot_de_passe_est_refuse(self):
        creer_membre("ines@exemple.test")
        reponse = se_connecter(self.client, "ines@exemple.test", "pas-le-bon")
        self.assertEqual(reponse.status_code, 200)  # on reste sur le formulaire, avec l'erreur
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_une_adresse_non_verifiee_ne_permet_pas_de_se_connecter(self):
        creer_membre("nouveau@exemple.test", adresse_verifiee=False)
        se_connecter(self.client, "nouveau@exemple.test")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_un_compte_en_attente_ne_se_connecte_pas_et_sait_pourquoi(self):
        creer_membre("attente@exemple.test", statut_inscription=Membre.StatutInscription.EN_ATTENTE)
        reponse = self.client.post(
            "/compte/login/",
            {"login": "attente@exemple.test", "password": MOT_DE_PASSE},
            follow=True,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(reponse, "en attente de validation")

    def test_un_compte_refuse_ne_se_connecte_pas_et_sait_pourquoi(self):
        creer_membre("refuse@exemple.test", statut_inscription=Membre.StatutInscription.REFUSEE)
        reponse = self.client.post(
            "/compte/login/",
            {"login": "refuse@exemple.test", "password": MOT_DE_PASSE},
            follow=True,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(reponse, "a été refusée")

    def test_la_deconnexion_ferme_la_session(self):
        creer_membre("ines@exemple.test")
        se_connecter(self.client, "ines@exemple.test")
        self.client.post("/compte/logout/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_l_inscription_reste_fermee_en_attendant_sa_pr(self):
        self.client.post(
            "/compte/signup/",
            {
                "email": "inconnu@exemple.test",
                "password1": "Un-mot-de-passe-long-1",
                "password2": "Un-mot-de-passe-long-1",
            },
        )
        self.assertFalse(Membre.objects.filter(email="inconnu@exemple.test").exists())


class MotsDePasseDatalumniTests(TestCase):
    """
    Authentik (la connexion de Datalumni) stocke les mots de passe au format Django pbkdf2_sha256.
    On fabrique une empreinte dans ce format, avec un mot de passe inventé.
    """

    def setUp(self):
        self.membre = creer_membre("importe@exemple.test")
        # Même algorithme que Django 5.2, avec moins d'itérations : une empreinte plus ancienne.
        empreinte = PBKDF2PasswordHasher().encode(
            "ancien-mot-de-passe", "selfactice1234", iterations=260000
        )
        # Comme le fera le script d'import de Luc : l'empreinte est copiée telle quelle.
        Membre.objects.filter(pk=self.membre.pk).update(password=empreinte)

    def test_un_membre_importe_se_connecte_avec_son_ancien_mot_de_passe(self):
        reponse = se_connecter(self.client, "importe@exemple.test", "ancien-mot-de-passe")
        self.assertRedirects(reponse, "/")

    def test_l_empreinte_est_renforcee_au_premier_login(self):
        se_connecter(self.client, "importe@exemple.test", "ancien-mot-de-passe")
        self.membre.refresh_from_db()
        algorithme, iterations, *_ = self.membre.password.split("$")
        self.assertEqual(algorithme, "pbkdf2_sha256")
        self.assertEqual(int(iterations), PBKDF2PasswordHasher.iterations)
