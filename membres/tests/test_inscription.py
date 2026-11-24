import re

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre

INSCRIPTION = reverse("account_signup")
CONNEXION = reverse("account_login")
ANNUAIRE = reverse("membres:annuaire")
MOT_DE_PASSE = "Bessieres-Promo-2019"
EMAIL = "lea.martin@exemple.test"


def formulaire(**champs):
    """Un formulaire d'inscription complet et valide ; `champs` remplace ou ajoute des valeurs."""
    donnees = {
        "email": EMAIL,
        "password1": MOT_DE_PASSE,
        "password2": MOT_DE_PASSE,
        "civilite": "madame",
        "prenom": "Léa",
        "nom": "Martin",
        "nom_de_naissance": "",
        "categorie": "alumni",
        "cgu": "on",
        "site_web": "",
    }
    donnees.update(champs)
    return donnees


class PageInscriptionTests(TestCase):
    def test_la_page_d_inscription_est_ouverte(self):
        reponse = self.client.get(INSCRIPTION)

        self.assertEqual(reponse.status_code, 200)
        for etape in ("1. Votre compte", "2. Vous", "3. Votre lien avec", "4. Conditions"):
            self.assertContains(reponse, etape)
        self.assertContains(reponse, 'href="/page/cgu/"')

    def test_la_page_de_connexion_mene_a_l_inscription(self):
        reponse = self.client.get(CONNEXION)

        self.assertContains(reponse, f'href="{INSCRIPTION}')


class InscriptionTests(TestCase):
    def setUp(self):
        # allauth limite les envois d'e-mails et les inscriptions (compteurs dans le cache) :
        # on repart à zéro à chaque test.
        cache.clear()

    def inscrire(self, **champs):
        # allauth envoie l'e-mail à la fin de la transaction : on exécute ces envois en test.
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(INSCRIPTION, formulaire(**champs), follow=True)

    def cliquer_le_lien_de_verification(self):
        lien = re.search(r"/compte/confirm-email/\S+/", mail.outbox[-1].body).group(0)
        return self.client.post(lien, follow=True)

    def test_une_inscription_cree_un_membre_valide_mais_pas_encore_connecte(self):
        reponse = self.inscrire()

        membre = Membre.objects.get(email=EMAIL)
        self.assertEqual((membre.prenom, membre.nom), ("Léa", "Martin"))
        self.assertEqual(membre.civilite, Membre.Civilite.MADAME)
        self.assertEqual(membre.categorie, Membre.Categorie.ALUMNI)
        self.assertEqual(membre.statut_inscription, Membre.StatutInscription.VALIDEE)
        self.assertTrue(membre.check_password(MOT_DE_PASSE))
        self.assertContains(reponse, "Il reste à vérifier votre adresse e-mail")
        self.assertEqual(mail.outbox[-1].to, [EMAIL])
        # Tant que l'adresse n'est pas vérifiée, personne n'est connecté.
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.get(ANNUAIRE), f"{CONNEXION}?next={ANNUAIRE}")

    def test_le_lien_de_verification_connecte_le_membre(self):
        self.inscrire()

        self.cliquer_le_lien_de_verification()

        self.assertEqual(self.client.get(ANNUAIRE).status_code, 200)

    def test_un_recruteur_attend_la_validation(self):
        self.inscrire(categorie="recruteur")
        membre = Membre.objects.get(email=EMAIL)
        self.assertEqual(membre.statut_inscription, Membre.StatutInscription.EN_ATTENTE)

        reponse = self.cliquer_le_lien_de_verification()

        self.assertContains(reponse, "Votre inscription est en attente de validation.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_on_ne_peut_pas_se_donner_de_statut_ni_de_droits(self):
        self.inscrire(
            categorie="recruteur",
            statut_inscription="validee",
            is_staff="on",
            is_superuser="on",
            groups="1",
        )

        membre = Membre.objects.get(email=EMAIL)
        self.assertEqual(membre.statut_inscription, Membre.StatutInscription.EN_ATTENTE)
        self.assertFalse(membre.is_staff)
        self.assertFalse(membre.is_superuser)
        self.assertFalse(membre.groups.exists())

    def test_un_compte_refuse_apres_coup_perd_l_acces_tout_de_suite(self):
        self.inscrire()
        self.cliquer_le_lien_de_verification()

        Membre.objects.filter(email=EMAIL).update(
            statut_inscription=Membre.StatutInscription.REFUSEE
        )

        self.assertEqual(self.client.get(ANNUAIRE).status_code, 403)

    def test_le_champ_piege_arrete_les_robots(self):
        reponse = self.client.post(INSCRIPTION, formulaire(site_web="https://spam.exemple.test"))

        self.assertEqual(reponse.status_code, 200)
        self.assertIn("site_web", reponse.context["form"].errors)
        self.assertFalse(Membre.objects.exists())

    def test_les_champs_obligatoires(self):
        for champ in ("prenom", "nom", "categorie", "cgu"):
            with self.subTest(champ=champ):
                donnees = formulaire()
                del donnees[champ]

                reponse = self.client.post(INSCRIPTION, donnees)

                self.assertEqual(reponse.status_code, 200)  # formulaire réaffiché
                self.assertIn(champ, reponse.context["form"].errors)
                self.assertFalse(Membre.objects.exists())

    def test_un_mot_de_passe_trop_faible_est_refuse(self):
        reponse = self.client.post(INSCRIPTION, formulaire(password1="123456", password2="123456"))

        self.assertIn("password1", reponse.context["form"].errors)
        self.assertFalse(Membre.objects.exists())

    def test_une_adresse_deja_inscrite_ne_cree_pas_de_second_compte(self):
        self.inscrire()
        self.client.logout()

        self.inscrire(email="LEA.Martin@exemple.test", prenom="Autre")

        self.assertEqual(Membre.objects.filter(email__iexact=EMAIL).count(), 1)
        self.assertEqual(Membre.objects.get().prenom, "Léa")

    def test_les_inscriptions_en_rafale_sont_limitees(self):
        # 5 par minute depuis une même adresse IP (ACCOUNT_RATE_LIMITS) : la 6e est refusée.
        for numero in range(5):
            self.client.post(INSCRIPTION, formulaire(email=f"robot{numero}@exemple.test"))

        reponse = self.client.post(INSCRIPTION, formulaire(email="robot5@exemple.test"))

        self.assertEqual(reponse.status_code, 429)
        self.assertEqual(Membre.objects.count(), 5)
