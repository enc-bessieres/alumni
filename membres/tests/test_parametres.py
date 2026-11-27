from django.conf import settings
from django.contrib.auth.models import Group
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre

PARAMETRES = reverse("membres:parametres")
ANNUAIRE = reverse("membres:annuaire")


def creer(prenom="Léa", nom="Martin", **champs):
    champs.setdefault("statut_inscription", Membre.StatutInscription.VALIDEE)
    return Membre.objects.create_user(
        f"{prenom}.{nom}@exemple.test".lower(),
        "motdepasse-de-test",
        prenom=prenom,
        nom=nom,
        **champs,
    )


class AccesParametresTests(TestCase):
    def test_un_visiteur_est_renvoye_vers_la_connexion(self):
        reponse = self.client.get(PARAMETRES)

        connexion = resolve_url(settings.LOGIN_URL)
        self.assertRedirects(
            reponse, f"{connexion}?next={PARAMETRES}", fetch_redirect_response=False
        )

    def test_un_membre_non_valide_recoit_une_403(self):
        self.client.force_login(creer(statut_inscription=Membre.StatutInscription.REFUSEE))

        self.assertEqual(self.client.get(PARAMETRES).status_code, 403)

    def test_la_zone_membre_mene_aux_parametres(self):
        self.client.force_login(creer())

        reponse = self.client.get(ANNUAIRE)

        self.assertContains(reponse, f'<a href="{PARAMETRES}">Paramètres</a>')


class ParametresTests(TestCase):
    def setUp(self):
        self.membre = creer()
        self.client.force_login(self.membre)

    def test_les_cases_sont_decochees_par_defaut(self):
        reponse = self.client.get(PARAMETRES)

        self.assertContains(reponse, '<input type="checkbox" name="visible_dans_annuaire"')
        self.assertContains(reponse, '<input type="checkbox" name="email_visible"')
        self.assertNotContains(reponse, "checked")

    def test_cocher_la_case_rend_visible_dans_l_annuaire(self):
        reponse = self.client.post(PARAMETRES, {"visible_dans_annuaire": "on"}, follow=True)

        self.assertRedirects(reponse, PARAMETRES)
        self.assertContains(reponse, "Vos paramètres sont enregistrés.")
        self.membre.refresh_from_db()
        self.assertTrue(self.membre.visible_dans_annuaire)
        annuaire = self.client.get(ANNUAIRE)
        self.assertIn(self.membre, annuaire.context["page"].object_list)

    def test_decocher_la_case_masque_le_membre(self):
        # Une case décochée n'est pas envoyée par le navigateur : le POST est vide.
        self.membre.visible_dans_annuaire = True
        self.membre.save()

        self.client.post(PARAMETRES, {})

        self.membre.refresh_from_db()
        self.assertFalse(self.membre.visible_dans_annuaire)
        annuaire = self.client.get(ANNUAIRE)
        self.assertNotIn(self.membre, annuaire.context["page"].object_list)

    def test_on_ne_peut_pas_se_donner_d_autres_droits(self):
        # Un champ ajouté à la main dans la requête est ignoré par le formulaire.
        administrateur = Group.objects.get(name="Administrateur")
        self.client.post(
            PARAMETRES,
            {
                "visible_dans_annuaire": "on",
                "is_staff": "on",
                "is_superuser": "on",
                "groups": [administrateur.pk],
                "email": "pirate@exemple.test",
                "statut_inscription": Membre.StatutInscription.EN_ATTENTE,
            },
        )

        self.membre.refresh_from_db()
        self.assertFalse(self.membre.is_staff)
        self.assertFalse(self.membre.is_superuser)
        self.assertFalse(self.membre.groups.exists())
        self.assertEqual(self.membre.email, "léa.martin@exemple.test")
        self.assertEqual(self.membre.statut_inscription, Membre.StatutInscription.VALIDEE)

    def test_on_ne_modifie_que_son_propre_compte(self):
        autre = creer("Hugo", "Lefevre")

        self.client.post(PARAMETRES, {"visible_dans_annuaire": "on"})

        autre.refresh_from_db()
        self.assertFalse(autre.visible_dans_annuaire)
