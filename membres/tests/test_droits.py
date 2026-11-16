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

    def test_un_administrateur_gere_les_droits(self):
        administrateur = creer("admin@exemple.test", groupe="Administrateur")
        self.assertTrue(administrateur.has_perm("membres.gerer_les_droits"))
        self.assertTrue(administrateur.has_perm("membres.delete_membre"))


class BackOfficeTests(TestCase):
    def champs_verrouilles(self, utilisateur):
        requete = RequestFactory().get("/")
        requete.user = utilisateur
        return site._registry[Membre].get_readonly_fields(requete)

    def test_un_validateur_valide_mais_ne_touche_pas_aux_droits(self):
        verrouilles = self.champs_verrouilles(creer("valid@exemple.test", groupe="Validateur"))
        self.assertNotIn("statut_inscription", verrouilles)
        for champ in ["groups", "is_staff", "user_permissions", "is_superuser"]:
            with self.subTest(champ=champ):
                self.assertIn(champ, verrouilles)

    def test_un_administrateur_donne_les_groupes_mais_pas_le_superutilisateur(self):
        verrouilles = self.champs_verrouilles(creer("adm@exemple.test", groupe="Administrateur"))
        self.assertNotIn("groups", verrouilles)
        self.assertNotIn("is_staff", verrouilles)
        self.assertIn("is_superuser", verrouilles)

    def test_un_validateur_ne_peut_pas_se_donner_le_groupe_administrateur(self):
        validateur = creer("ambitieux@exemple.test", groupe="Validateur")
        self.client.force_login(validateur)
        fiche = f"/admin/membres/membre/{validateur.pk}/change/"
        reponse = self.client.get(fiche)
        formulaire = reponse.context["adminform"].form
        donnees = {
            nom: formulaire.initial.get(nom, "") or ""
            for nom in formulaire.fields
            if nom not in ("password",)
        }
        donnees["groups"] = [Group.objects.get(name="Administrateur").pk]
        reponse = self.client.post(fiche, donnees)
        self.assertEqual(reponse.status_code, 302)  # la fiche est bien enregistrée…
        validateur.refresh_from_db()  # … mais sans le groupe demandé
        self.assertFalse(validateur.groups.filter(name="Administrateur").exists())

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
