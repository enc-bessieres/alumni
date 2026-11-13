from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.test import TestCase

from membres.models import Membre


def creer(email, mot_de_passe="motdepasse-de-test", **champs):
    champs.setdefault("prenom", "Test")
    champs.setdefault("nom", "Exemple")
    champs.setdefault("categorie", Membre.Categorie.ALUMNI)
    return Membre.objects.create_user(email, mot_de_passe, **champs)


class MembreTests(TestCase):
    def test_un_membre_se_cree_avec_son_e_mail_sans_identifiant(self):
        membre = creer("Ines.Martin@Exemple.test", prenom="Inès", nom="Martin")
        self.assertEqual(membre.email, "ines.martin@exemple.test")  # tout en minuscules
        self.assertTrue(membre.password.startswith("pbkdf2_sha256$"))  # jamais en clair
        self.assertEqual(membre.statut_inscription, Membre.StatutInscription.EN_ATTENTE)
        self.assertEqual(membre.role, Membre.Role.MEMBRE)
        self.assertIsNotNone(membre.cree_le)  # date de création, posée automatiquement
        self.assertIsNone(membre.last_login)  # dernière connexion : jamais connecté
        self.assertEqual(str(membre), "Inès Martin")

    def test_civilite_et_nom_de_naissance_sont_facultatifs(self):
        membre = creer(
            "lina@exemple.test", civilite=Membre.Civilite.MADAME, nom_de_naissance="Haddad"
        )
        self.assertEqual(membre.get_civilite_display(), "Madame")
        self.assertEqual(membre.nom_de_naissance, "Haddad")

    def test_deux_membres_ne_partagent_pas_un_e_mail(self):
        creer("double@exemple.test")
        with self.assertRaises(IntegrityError):
            creer("double@exemple.test")

    def test_la_casse_ne_cree_pas_de_doublon(self):
        creer("ines.martin@exemple.test")
        with self.assertRaises(IntegrityError):
            creer(" Ines.Martin@Exemple.TEST ")

    def test_la_base_refuse_un_doublon_de_casse_meme_sans_passer_par_save(self):
        # Un import en masse (bulk_create) contourne save() : la contrainte de la base le bloque.
        creer("lina@exemple.test")
        with self.assertRaises(IntegrityError):
            Membre.objects.bulk_create(
                [
                    Membre(
                        email="LINA@exemple.test", prenom="Lina", nom="Doublon", categorie="alumni"
                    )
                ]
            )

    def test_la_connexion_ignore_la_casse_de_l_e_mail(self):
        membre = creer("hugo.benali@exemple.test", mot_de_passe="motdepasse-de-test")
        retrouve = authenticate(email="Hugo.Benali@Exemple.test", password="motdepasse-de-test")
        self.assertEqual(retrouve, membre)

    def test_le_back_office_enregistre_l_e_mail_en_minuscules(self):
        membre = Membre(email="Theo@Exemple.test", prenom="Théo", nom="Petit", categorie="alumni")
        membre.full_clean(exclude=["password"])  # ce que fait un formulaire avant d'enregistrer
        self.assertEqual(membre.email, "theo@exemple.test")

    def test_un_compte_importe_sans_mot_de_passe_ne_peut_pas_se_connecter(self):
        membre = creer("importe@exemple.test", mot_de_passe=None)
        self.assertFalse(membre.has_usable_password())

    def test_le_superutilisateur_est_administrateur_et_valide(self):
        admin = Membre.objects.create_superuser(
            "admin@exemple.test", "motdepasse-de-test", prenom="Admin", nom="Exemple"
        )
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, Membre.Role.ADMINISTRATEUR)
        self.assertEqual(admin.statut_inscription, Membre.StatutInscription.VALIDEE)
