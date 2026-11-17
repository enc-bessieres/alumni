import warnings
from unittest import mock

from django.contrib.admin.sites import site
from django.contrib.auth.models import Group, Permission
from django.test import RequestFactory, TestCase

from membres import droits
from membres.models import Membre


def creer(email, groupe=None, **champs):
    """Un membre validé ; avec `groupe`, il reçoit aussi ce rôle et l'accès au back-office."""
    champs.setdefault("categorie", Membre.Categorie.ALUMNI)
    champs.setdefault("statut_inscription", Membre.StatutInscription.VALIDEE)
    if groupe:
        champs["is_staff"] = True
    membre = Membre.objects.create_user(
        email, "motdepasse-de-test", prenom="Test", nom=email, **champs
    )
    if groupe:
        membre.groups.add(Group.objects.get(name=groupe))
    return membre


class GroupesTests(TestCase):
    def test_migrate_cree_les_groupes_avec_leurs_permissions(self):
        for nom, codes in droits.GROUPES.items():
            with self.subTest(groupe=nom):
                groupe = Group.objects.get(name=nom)
                obtenues = {
                    f"{p.content_type.app_label}.{p.codename}" for p in groupe.permissions.all()
                }
                self.assertEqual(obtenues, set(codes))

    def test_toutes_les_permissions_des_groupes_existent(self):
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

    def test_un_validateur_peut_valider_une_inscription(self):
        validateur = creer("validateur@exemple.test", groupe="Validateur")
        self.assertTrue(validateur.has_perm("membres.valider_inscription"))
        self.assertFalse(validateur.has_perm("membres.gerer_les_droits"))

    def test_un_membre_sans_groupe_n_a_aucun_droit(self):
        membre = creer("membre@exemple.test")
        self.assertFalse(membre.has_perm("membres.valider_inscription"))
        self.assertFalse(membre.has_perm("membres.change_membre"))

    def test_une_faute_de_frappe_dans_les_groupes_est_signalee(self):
        groupes = {**droits.GROUPES, "Essai": ["membres.gerer_les_droitz", "membre.view_membre"]}
        with mock.patch.object(droits, "GROUPES", groupes):
            with warnings.catch_warnings(record=True) as alertes:
                warnings.simplefilter("always")
                droits.creer_groupes()
        messages = " ".join(str(alerte.message) for alerte in alertes)
        self.assertIn("membres.gerer_les_droitz", messages)  # application connue, code inconnu
        self.assertIn("membre.view_membre", messages)  # application inconnue
        self.assertFalse(Group.objects.filter(name="Essai").exists())

    def test_l_administrateur_gere_les_referentiels(self):
        administrateur = creer("admin@exemple.test", groupe="Administrateur")
        self.assertTrue(administrateur.has_perm("referentiels.change_diplome"))
        self.client.force_login(administrateur)
        self.assertEqual(self.client.get("/admin/referentiels/diplome/").status_code, 200)

    def test_un_administrateur_gere_les_droits(self):
        administrateur = creer("admin@exemple.test", groupe="Administrateur")
        self.assertTrue(administrateur.has_perm("membres.gerer_les_droits"))
        self.assertTrue(administrateur.has_perm("membres.delete_membre"))


class BackOfficeTests(TestCase):
    def champs_verrouilles(self, utilisateur):
        requete = RequestFactory().get("/")
        requete.user = utilisateur
        return site._registry[Membre].get_readonly_fields(requete)

    def test_un_validateur_ne_modifie_que_le_statut_de_l_inscription(self):
        verrouilles = self.champs_verrouilles(creer("valid@exemple.test", groupe="Validateur"))
        self.assertNotIn("statut_inscription", verrouilles)
        for champ in ["email", "prenom", "is_active", "groups", "is_staff", "user_permissions"]:
            with self.subTest(champ=champ):
                self.assertIn(champ, verrouilles)

    def test_un_validateur_valide_une_inscription(self):
        self.client.force_login(creer("valid@exemple.test", groupe="Validateur"))
        inscrit = creer("inscrit@exemple.test", statut_inscription="en_attente")
        reponse = self.client.post(
            f"/admin/membres/membre/{inscrit.pk}/change/", {"statut_inscription": "validee"}
        )
        self.assertRedirects(reponse, "/admin/membres/membre/")
        inscrit.refresh_from_db()
        self.assertEqual(inscrit.statut_inscription, Membre.StatutInscription.VALIDEE)

    def test_un_validateur_ne_change_pas_le_mot_de_passe_d_un_membre(self):
        self.client.force_login(creer("valid@exemple.test", groupe="Validateur"))
        membre = creer("membre@exemple.test")
        fiche = self.client.get(f"/admin/membres/membre/{membre.pk}/change/")
        self.assertNotContains(fiche, "/password/")  # pas de lien vers le formulaire
        page = self.client.get(f"/admin/membres/membre/{membre.pk}/password/")
        self.assertEqual(page.status_code, 403)

    def test_un_validateur_ne_change_ni_l_e_mail_ni_l_activation_d_un_membre(self):
        self.client.force_login(creer("valid@exemple.test", groupe="Validateur"))
        membre = creer("membre@exemple.test", statut_inscription="en_attente")
        self.client.post(
            f"/admin/membres/membre/{membre.pk}/change/",
            {"statut_inscription": "validee", "email": "pirate@exemple.test", "is_active": ""},
        )
        membre.refresh_from_db()
        self.assertEqual(membre.statut_inscription, Membre.StatutInscription.VALIDEE)
        self.assertEqual(membre.email, "membre@exemple.test")  # champ ignoré
        self.assertTrue(membre.is_active)  # champ ignoré

    def test_un_validateur_ne_modifie_pas_le_compte_d_un_membre_de_l_equipe(self):
        self.client.force_login(creer("valid@exemple.test", groupe="Validateur"))
        admin = creer("admin@exemple.test", groupe="Administrateur")
        fiche = f"/admin/membres/membre/{admin.pk}/"
        reponse = self.client.post(fiche + "change/", {"statut_inscription": "refusee"})
        self.assertEqual(reponse.status_code, 403)
        admin.refresh_from_db()
        self.assertEqual(admin.statut_inscription, Membre.StatutInscription.VALIDEE)
        self.assertEqual(self.client.get(fiche + "password/").status_code, 403)

    def test_un_administrateur_donne_les_groupes_mais_pas_les_permissions(self):
        verrouilles = self.champs_verrouilles(creer("adm@exemple.test", groupe="Administrateur"))
        self.assertNotIn("groups", verrouilles)
        self.assertNotIn("is_staff", verrouilles)
        self.assertIn("is_superuser", verrouilles)
        self.assertIn("user_permissions", verrouilles)

    def test_un_administrateur_change_le_mot_de_passe_d_un_membre(self):
        self.client.force_login(creer("adm@exemple.test", groupe="Administrateur"))
        membre = creer("oubli@exemple.test")
        page = self.client.get(f"/admin/membres/membre/{membre.pk}/password/")
        self.assertEqual(page.status_code, 200)

    def test_un_compte_avec_un_groupe_est_protege_meme_sans_acces_au_back_office(self):
        self.client.force_login(creer("valid@exemple.test", groupe="Validateur"))
        administrateur = creer("admin@exemple.test")
        administrateur.groups.add(Group.objects.get(name="Administrateur"))  # sans is_staff
        reponse = self.client.post(
            f"/admin/membres/membre/{administrateur.pk}/change/", {"statut_inscription": "refusee"}
        )
        self.assertEqual(reponse.status_code, 403)
        administrateur.refresh_from_db()
        self.assertEqual(administrateur.statut_inscription, Membre.StatutInscription.VALIDEE)

    def test_seul_un_superutilisateur_touche_au_compte_d_un_superutilisateur(self):
        self.client.force_login(creer("adm@exemple.test", groupe="Administrateur"))
        chef = Membre.objects.create_superuser(
            "chef@exemple.test", "motdepasse-de-test", prenom="Chef", nom="Exemple"
        )
        fiche = f"/admin/membres/membre/{chef.pk}/"
        # Il voit la fiche (droit de consultation), mais en lecture seule.
        self.assertFalse(self.client.get(fiche + "change/").context["has_change_permission"])
        reponse = self.client.post(fiche + "change/", {"email": "pirate@exemple.test"})
        self.assertEqual(reponse.status_code, 403)
        for page in ["password", "delete"]:
            with self.subTest(page=page):
                self.assertEqual(self.client.get(fiche + page + "/").status_code, 403)
        # La suppression en masse depuis la liste est bloquée aussi.
        self.client.post(
            "/admin/membres/membre/",
            {"action": "delete_selected", "_selected_action": [chef.pk], "post": "yes"},
        )
        self.assertTrue(Membre.objects.filter(pk=chef.pk).exists())

    def test_un_validateur_ne_peut_pas_se_donner_le_groupe_administrateur(self):
        validateur = creer("ambitieux@exemple.test", groupe="Validateur")
        self.client.force_login(validateur)
        administrateur = Group.objects.get(name="Administrateur")
        reponse = self.client.post(
            f"/admin/membres/membre/{validateur.pk}/change/", {"groups": [administrateur.pk]}
        )
        self.assertEqual(reponse.status_code, 403)  # son compte est celui d'un membre de l'équipe
        self.assertFalse(validateur.groups.filter(pk=administrateur.pk).exists())

    def test_seuls_les_comptes_du_back_office_y_ont_acces(self):
        # Le back-office de Django n'ouvre qu'aux comptes « accès au back-office » (is_staff).
        requete = RequestFactory().get("/admin/")
        requete.user = creer("curieux@exemple.test")
        self.assertFalse(site.has_permission(requete))
        requete.user = creer("valide@exemple.test", groupe="Validateur")
        self.assertTrue(site.has_permission(requete))

    def test_l_administrateur_cree_un_membre_dans_le_back_office(self):
        self.client.force_login(creer("admin@exemple.test", groupe="Administrateur"))
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

    def test_la_fiche_d_un_membre_s_affiche_avec_ses_groupes(self):
        self.client.force_login(creer("admin@exemple.test", groupe="Administrateur"))
        membre = creer("fiche@exemple.test")
        reponse = self.client.get(f"/admin/membres/membre/{membre.pk}/change/")
        self.assertContains(reponse, "Nom de naissance")
        self.assertContains(reponse, "Rôle et droits")
