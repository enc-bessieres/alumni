from django.contrib.admin.sites import site
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase

from membres import droits
from membres.models import Membre


def creer(email, **champs):
    champs.setdefault("categorie", Membre.Categorie.ALUMNI)
    champs.setdefault("statut_inscription", Membre.StatutInscription.VALIDEE)
    return Membre.objects.create_user(
        email, "motdepasse-de-test", prenom="Test", nom=email, **champs
    )


class DroitsTests(TestCase):
    def test_toutes_les_permissions_des_roles_existent(self):
        # Attrape une faute de frappe dans membres/droits.py.
        for groupe, codes in droits.GROUPES.items():
            for code in codes:
                app_label, codename = code.split(".")
                with self.subTest(groupe=groupe, permission=code):
                    self.assertTrue(
                        Permission.objects.filter(
                            content_type__app_label=app_label, codename=codename
                        ).exists()
                    )

    def test_un_membre_accepte_consulte_l_annuaire_mais_pas_le_back_office(self):
        membre = creer("membre@exemple.test")
        self.assertTrue(membre.has_perm("membres.consulter_annuaire"))
        self.assertFalse(membre.is_staff)

    def test_un_membre_en_attente_ne_consulte_pas_l_annuaire(self):
        membre = creer(
            "attente@exemple.test", statut_inscription=Membre.StatutInscription.EN_ATTENTE
        )
        self.assertFalse(membre.has_perm("membres.consulter_annuaire"))

    def test_changer_le_role_met_a_jour_les_droits(self):
        membre = creer("promu@exemple.test")
        membre.role = Membre.Role.VALIDATEUR
        membre.save()
        membre = Membre.objects.get(pk=membre.pk)  # recharge, pour vider le cache des permissions
        self.assertTrue(membre.is_staff)
        self.assertTrue(membre.has_perm("membres.valider_inscription"))
        self.assertFalse(membre.has_perm("membres.changer_role"))

    def test_seul_l_administrateur_peut_modifier_le_role_dans_le_back_office(self):
        admin_membres = site._registry[Membre]
        requete = RequestFactory().get("/")

        requete.user = creer("validateur@exemple.test", role=Membre.Role.VALIDATEUR)
        self.assertIn("role", admin_membres.get_readonly_fields(requete))
        self.assertNotIn("statut_inscription", admin_membres.get_readonly_fields(requete))

        requete.user = creer("admin@exemple.test", role=Membre.Role.ADMINISTRATEUR)
        self.assertNotIn("role", admin_membres.get_readonly_fields(requete))

    def test_un_simple_membre_n_entre_pas_dans_le_back_office(self):
        self.client.force_login(creer("curieux@exemple.test"))
        reponse = self.client.get("/admin/")
        self.assertRedirects(reponse, "/admin/login/?next=/admin/")


class BackOfficeTests(TestCase):
    def setUp(self):
        self.client.force_login(creer("admin@exemple.test", role=Membre.Role.ADMINISTRATEUR))

    def test_l_administrateur_cree_un_membre_dans_le_back_office(self):
        reponse = self.client.post(
            "/admin/membres/membre/add/",
            {
                "email": "nouveau@exemple.test",
                "prenom": "Hugo",
                "nom": "Benali",
                "categorie": Membre.Categorie.ETUDIANT,
                "usable_password": "true",
                "password1": "Un-mot-de-passe-long-2026",
                "password2": "Un-mot-de-passe-long-2026",
            },
        )
        self.assertEqual(reponse.status_code, 302)  # renvoi vers la fiche : création réussie
        self.assertTrue(Membre.objects.filter(email="nouveau@exemple.test").exists())

    def test_la_fiche_d_un_membre_s_affiche(self):
        membre = creer("fiche@exemple.test")
        reponse = self.client.get(f"/admin/membres/membre/{membre.pk}/change/")
        self.assertContains(reponse, "Nom de naissance")
