from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from membres.models import Experience, Membre

PROFIL = reverse("membres:profil")


def creer(prenom="Lea", nom="Martin", **champs):
    champs.setdefault("statut_inscription", Membre.StatutInscription.VALIDEE)
    return Membre.objects.create_user(
        f"{prenom}.{nom}@exemple.test".lower(),
        "motdepasse-de-test",
        prenom=prenom,
        nom=nom,
        **champs,
    )


def parcours(*experiences, initiales=0):
    """Les données envoyées par le formulaire du parcours (jeu de formulaires « parcours »)."""
    donnees = {
        "parcours-TOTAL_FORMS": str(len(experiences)),
        "parcours-INITIAL_FORMS": str(initiales),
        "parcours-MIN_NUM_FORMS": "0",
        "parcours-MAX_NUM_FORMS": "20",
    }
    for i, experience in enumerate(experiences):
        for champ, valeur in experience.items():
            donnees[f"parcours-{i}-{champ}"] = valeur
    return donnees


COMPTABLE = {"intitule": "Comptable", "organisation": "Cabinet Exemple Audit", "debut": "2018"}


class AccesProfilTests(TestCase):
    def test_un_visiteur_est_renvoye_vers_la_connexion(self):
        reponse = self.client.get(PROFIL)

        connexion = resolve_url(settings.LOGIN_URL)
        self.assertRedirects(reponse, f"{connexion}?next={PROFIL}", fetch_redirect_response=False)

    def test_un_membre_non_valide_recoit_une_403(self):
        self.client.force_login(creer(statut_inscription=Membre.StatutInscription.EN_ATTENTE))

        self.assertEqual(self.client.get(PROFIL).status_code, 403)

    def test_la_zone_membre_mene_au_profil(self):
        self.client.force_login(creer())

        reponse = self.client.get(reverse("membres:annuaire"))

        self.assertContains(reponse, f'<a href="{PROFIL}">Profil</a>', html=True)


class ParcoursTests(TestCase):
    def setUp(self):
        self.membre = creer()
        self.client.force_login(self.membre)

    def test_ajouter_une_experience(self):
        reponse = self.client.post(PROFIL, parcours(COMPTABLE), follow=True)

        self.assertRedirects(reponse, PROFIL)
        self.assertContains(reponse, "Votre parcours est enregistré.")
        experience = self.membre.experiences.get()
        self.assertEqual(str(experience), "Comptable — Cabinet Exemple Audit")
        self.assertTrue(experience.poste_actuel)  # pas d'année de fin

    def test_modifier_puis_supprimer_une_experience(self):
        experience = Experience.objects.create(membre=self.membre, **COMPTABLE)
        modifiee = {"id": str(experience.pk), **COMPTABLE, "fin": "2022"}

        self.client.post(PROFIL, parcours(modifiee, initiales=1))
        experience.refresh_from_db()
        self.assertEqual(experience.fin, 2022)

        self.client.post(PROFIL, parcours({**modifiee, "DELETE": "on"}, initiales=1))
        self.assertFalse(self.membre.experiences.exists())

    def test_les_annees_sont_controlees(self):
        annee_prochaine = str(timezone.now().year + 1)
        for erreur in [
            {**COMPTABLE, "fin": "2010"},  # fin avant le début
            {**COMPTABLE, "debut": annee_prochaine},  # début dans le futur
            {**COMPTABLE, "debut": "1900"},  # trop ancien
        ]:
            with self.subTest(erreur=erreur):
                reponse = self.client.post(PROFIL, parcours(erreur))

                self.assertEqual(reponse.status_code, 200)  # formulaire réaffiché
                self.assertFalse(reponse.context["parcours"].is_valid())
                self.assertFalse(self.membre.experiences.exists())

    def test_on_ne_peut_pas_modifier_l_experience_d_un_autre(self):
        autre = creer("Hugo", "Lefevre")
        sienne = Experience.objects.create(membre=autre, **COMPTABLE)

        # On envoie l'identifiant de l'expérience d'Hugo comme si c'était la nôtre.
        self.client.post(PROFIL, parcours({"id": str(sienne.pk), **COMPTABLE, "fin": "2019"}))
        self.client.post(
            PROFIL, parcours({"id": str(sienne.pk), **COMPTABLE, "DELETE": "on"}, initiales=1)
        )

        # L'expérience d'Hugo n'a pas bougé : ni modifiée, ni supprimée, ni rattachée à Léa.
        sienne.refresh_from_db()
        self.assertEqual(sienne.membre, autre)
        self.assertIsNone(sienne.fin)


class ParcoursSurLaFicheTests(TestCase):
    def test_le_parcours_apparait_sur_la_fiche(self):
        lea = creer()
        Experience.objects.create(membre=lea, **COMPTABLE, secteur="Comptabilité", lieu="Lyon")
        Experience.objects.create(
            membre=lea, intitule="Assistante", organisation="Studio Factice", debut=2014, fin=2017
        )
        self.client.force_login(creer("Ines", "Lecteur"))

        reponse = self.client.get(reverse("membres:fiche", args=[lea.pk]))

        contenu = " ".join(
            reponse.content.decode().split()
        )  # espaces et retours à la ligne réduits
        self.assertIn("<strong>Comptable</strong>, Cabinet Exemple Audit", contenu)
        self.assertIn("(2018 – aujourd'hui)", contenu)
        self.assertIn("(2014 – 2017)", contenu)
        self.assertContains(reponse, "Comptabilité · Lyon")
        # Le poste actuel avant les anciens.
        self.assertLess(contenu.index("Comptable"), contenu.index("Assistante"))
