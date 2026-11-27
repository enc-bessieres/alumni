"""
Le mentorat : se déclarer mentor ou mentoré.
Membres et adresses inventés (règle 1).
"""

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre

from .models import NB_MAX_MENTORES, ProfilMentorat, Sujet

ADRESSE = reverse("mentorat:mes_preferences")


def creer_membre(email, statut=Membre.StatutInscription.VALIDEE):
    return Membre.objects.create_user(
        email,
        "motdepasse-de-test",
        prenom="Test",
        nom="Test",
        categorie=Membre.Categorie.ALUMNI,
        statut_inscription=statut,
    )


class PreferencesMentoratTests(TestCase):
    def setUp(self):
        self.membre = creer_membre("ines@exemple.test")
        self.client.force_login(self.membre)
        self.orientation = Sujet.objects.create(nom="Orientation")
        self.reseau = Sujet.objects.create(nom="Réseau professionnel")

    def test_un_visiteur_non_connecte_est_renvoye_vers_la_connexion(self):
        self.client.logout()

        reponse = self.client.get(ADRESSE)

        connexion = resolve_url(settings.LOGIN_URL)
        self.assertRedirects(reponse, f"{connexion}?next={ADRESSE}", fetch_redirect_response=False)

    def test_un_membre_pas_encore_valide_n_y_a_pas_acces(self):
        en_attente = creer_membre("noe@exemple.test", Membre.StatutInscription.EN_ATTENTE)
        self.client.force_login(en_attente)

        reponse = self.client.post(ADRESSE, {"role": "mentor", "nb_max_mentores": 1})

        self.assertEqual(reponse.status_code, 403)
        self.assertFalse(ProfilMentorat.objects.filter(membre=en_attente).exists())

    def test_un_membre_se_declare_mentor(self):
        donnees = {"role": "mentor", "sujets": [self.orientation.pk], "nb_max_mentores": 3}

        reponse = self.client.post(ADRESSE, donnees, follow=True)

        profil = ProfilMentorat.objects.get(membre=self.membre)
        self.assertEqual(profil.role, ProfilMentorat.Role.MENTOR)
        self.assertEqual(list(profil.sujets.all()), [self.orientation])
        self.assertEqual(profil.nb_max_mentores, 3)
        self.assertContains(reponse, "Vos préférences de mentorat sont enregistrées.")

    def test_un_mentore_n_a_pas_de_nombre_maximum_de_mentores(self):
        donnees = {"role": "mentore", "sujets": [self.reseau.pk], "nb_max_mentores": 5}

        self.client.post(ADRESSE, donnees)

        profil = ProfilMentorat.objects.get(membre=self.membre)
        self.assertEqual(profil.role, ProfilMentorat.Role.MENTORE)
        self.assertEqual(profil.nb_max_mentores, 1)

    def test_un_membre_peut_etre_mentor_et_mentore(self):
        donnees = {"role": "mentor_et_mentore", "nb_max_mentores": 2}

        self.client.post(ADRESSE, donnees)

        profil = ProfilMentorat.objects.get(membre=self.membre)
        self.assertTrue(profil.accompagne)
        self.assertEqual(profil.nb_max_mentores, 2)

    def test_un_membre_modifie_ses_preferences(self):
        ProfilMentorat.objects.create(membre=self.membre, role=ProfilMentorat.Role.MENTORE)

        self.client.post(ADRESSE, {"role": "mentor", "nb_max_mentores": 2})

        profil = ProfilMentorat.objects.get(membre=self.membre)
        self.assertEqual(profil.role, ProfilMentorat.Role.MENTOR)
        self.assertEqual(profil.nb_max_mentores, 2)

    def test_un_membre_arrete_le_mentorat(self):
        ProfilMentorat.objects.create(membre=self.membre, role=ProfilMentorat.Role.MENTOR)

        reponse = self.client.post(ADRESSE, {"role": "", "nb_max_mentores": 1}, follow=True)

        self.assertFalse(ProfilMentorat.objects.filter(membre=self.membre).exists())
        self.assertContains(reponse, "Vous ne participez pas au mentorat.")

    def test_un_mentor_indique_son_nombre_maximum_de_mentores(self):
        reponse = self.client.post(ADRESSE, {"role": "mentor", "nb_max_mentores": ""})

        self.assertContains(reponse, "Indiquez combien de membres vous pouvez accompagner.")
        self.assertFalse(ProfilMentorat.objects.exists())

    def test_le_nombre_de_mentores_est_borne(self):
        for nombre in (0, NB_MAX_MENTORES + 1):
            with self.subTest(nombre=nombre):
                donnees = {"role": "mentor", "nb_max_mentores": nombre}

                reponse = self.client.post(ADRESSE, donnees)

                self.assertEqual(reponse.status_code, 200)  # le formulaire est réaffiché
                self.assertFalse(ProfilMentorat.objects.exists())

    def test_on_ne_modifie_que_son_propre_profil(self):
        autre = creer_membre("bruno@exemple.test")
        ProfilMentorat.objects.create(membre=autre, role=ProfilMentorat.Role.MENTOR)

        # Même en ajoutant « membre » aux données envoyées : le formulaire n'a pas ce champ.
        self.client.post(ADRESSE, {"role": "mentore", "nb_max_mentores": 1, "membre": autre.pk})

        self.assertEqual(ProfilMentorat.objects.get(membre=autre).role, "mentor")
        self.assertEqual(ProfilMentorat.objects.get(membre=self.membre).role, "mentore")

    def test_la_page_lie_la_charte_du_mentorat(self):
        reponse = self.client.get(ADRESSE)

        charte = reverse("pages_libres:detail", args=["charte-du-mentorat"])
        self.assertContains(reponse, f'href="{charte}"')

    def test_sans_sujet_la_page_le_signale(self):
        Sujet.objects.all().delete()

        reponse = self.client.get(ADRESSE)

        self.assertContains(reponse, "À COMPLÉTER : la liste des sujets de mentorat")
