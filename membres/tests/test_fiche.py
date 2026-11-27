from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre
from referentiels.models import Diplome, Formation, Site

PARAMETRES = reverse("membres:parametres")


def creer(prenom, nom, **champs):
    """Un membre validé et visible dans l'annuaire."""
    champs.setdefault("statut_inscription", Membre.StatutInscription.VALIDEE)
    champs.setdefault("visible_dans_annuaire", True)
    return Membre.objects.create_user(
        f"{prenom}.{nom}@exemple.test".lower(),
        "motdepasse-de-test",
        prenom=prenom,
        nom=nom,
        **champs,
    )


def fiche(membre):
    return reverse("membres:fiche", args=[membre.pk])


class AccesFicheTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lecteur = creer("Ines", "Lecteur")
        cls.lea = creer("Lea", "Martin")

    def test_un_visiteur_est_renvoye_vers_la_connexion(self):
        reponse = self.client.get(fiche(self.lea))

        connexion = resolve_url(settings.LOGIN_URL)
        self.assertRedirects(
            reponse, f"{connexion}?next={fiche(self.lea)}", fetch_redirect_response=False
        )

    def test_un_membre_non_valide_recoit_une_403(self):
        refuse = creer("Rita", "Refus", statut_inscription=Membre.StatutInscription.REFUSEE)
        self.client.force_login(refuse)

        self.assertEqual(self.client.get(fiche(self.lea)).status_code, 403)

    def test_la_fiche_d_un_membre_hors_annuaire_n_existe_pas(self):
        # Masqué, en attente, refusé, inactif ou jamais activé (#85) : 404, comme s'il n'existait
        # pas.
        absents = [
            creer("Jamais", "Active", compte_active=False),
            creer("Kenza", "Masquee", visible_dans_annuaire=False),
            creer("Paul", "Attente", statut_inscription=Membre.StatutInscription.EN_ATTENTE),
            creer("Rita", "Refus", statut_inscription=Membre.StatutInscription.REFUSEE),
            creer("Ancien", "Inactif", is_active=False),
        ]
        self.client.force_login(self.lecteur)
        for membre in absents:
            with self.subTest(membre=str(membre)):
                self.assertEqual(self.client.get(fiche(membre)).status_code, 404)

    def test_on_voit_sa_propre_fiche_meme_masquee(self):
        masque = creer("Kenza", "Masquee", visible_dans_annuaire=False)
        self.client.force_login(masque)

        reponse = self.client.get(fiche(masque))

        self.assertContains(reponse, "vous seul la voyez")

    def test_l_annuaire_mene_aux_fiches(self):
        self.client.force_login(self.lecteur)

        reponse = self.client.get(reverse("membres:annuaire"), {"q": "lea"})

        self.assertContains(reponse, f'<a href="{fiche(self.lea)}">Lea Martin</a>', html=True)


class ContenuFicheTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lecteur = creer("Ines", "Lecteur")
        cls.lea = creer("Lea", "Martin", categorie=Membre.Categorie.ALUMNI)
        Formation.objects.create(
            membre=cls.lea,
            diplome=Diplome.objects.get(nom="BTS SIO"),
            site=Site.objects.get(nom="ENC Bessières"),
            promo=2020,
        )

    def setUp(self):
        self.client.force_login(self.lecteur)

    def test_affiche_le_nom_la_categorie_et_les_diplomes(self):
        reponse = self.client.get(fiche(self.lea))

        self.assertContains(reponse, "<h1>Lea Martin</h1>", html=True)
        self.assertContains(reponse, "Alumni")
        self.assertContains(reponse, "BTS SIO, promo 2020 — ENC Bessières")

    def test_l_e_mail_est_cache_par_defaut(self):
        reponse = self.client.get(fiche(self.lea))

        self.assertNotContains(reponse, "lea.martin@exemple.test")
        self.assertNotContains(reponse, "LinkedIn")

    def test_l_e_mail_apparait_si_le_membre_l_a_choisi(self):
        self.lea.email_visible = True
        self.lea.save()

        reponse = self.client.get(fiche(self.lea))

        self.assertContains(reponse, 'href="mailto:lea.martin@exemple.test"')

    def test_le_profil_linkedin_apparait_s_il_est_renseigne(self):
        self.lea.linkedin = "https://www.linkedin.com/in/lea-martin/"
        self.lea.save()

        reponse = self.client.get(fiche(self.lea))

        self.assertContains(
            reponse,
            '<a href="https://www.linkedin.com/in/lea-martin/" target="_blank" '
            'rel="noopener noreferrer">Profil LinkedIn</a>',
            html=True,
        )


class ParametresFicheTests(TestCase):
    def setUp(self):
        self.membre = creer("Lea", "Martin")
        self.client.force_login(self.membre)

    def envoyer(self, **donnees):
        donnees.setdefault("visible_dans_annuaire", "on")
        reponse = self.client.post(PARAMETRES, donnees)
        self.membre.refresh_from_db()
        return reponse

    def test_montrer_son_e_mail(self):
        self.envoyer(email_visible="on")

        self.assertTrue(self.membre.email_visible)

    def test_enregistrer_son_profil_linkedin(self):
        self.envoyer(linkedin="https://www.linkedin.com/in/lea-martin/")

        self.assertEqual(self.membre.linkedin, "https://www.linkedin.com/in/lea-martin/")

    def test_une_adresse_qui_n_est_pas_un_profil_linkedin_est_refusee(self):
        for adresse in [
            "javascript:alert(1)",
            "https://site-pirate.exemple.test/in/lea",
            "https://www.linkedin.com.pirate.test/in/lea",
            "http://www.linkedin.com/in/lea",  # pas en https
            "https://www.linkedin.com/company/enc",  # pas un profil
        ]:
            with self.subTest(adresse=adresse):
                reponse = self.envoyer(linkedin=adresse)

                self.assertEqual(reponse.status_code, 200)  # le formulaire est réaffiché
                self.assertIn("linkedin", reponse.context["formulaire"].errors)
                self.assertContains(reponse, 'class="errorlist"')
                self.assertEqual(self.membre.linkedin, "")
