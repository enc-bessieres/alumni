"""La commande charger_donnees_dev, testée sur la base de test."""

from io import StringIO

from django.contrib.auth import authenticate
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from membres.models import Membre
from referentiels.models import Diplome, Formation

from .fausses_donnees import NOMBRE_PAR_DEFAUT


def charger(*arguments):
    sortie = StringIO()
    call_command("charger_donnees_dev", *arguments, stdout=sortie)
    return sortie.getvalue()


# Les tests tournent toujours avec DEBUG=False : on se met « en développement ».
@override_settings(DEBUG=True)
class ChargerDonneesDevTests(TestCase):
    def test_cree_les_1222_membres_de_l_annuaire_par_defaut(self):
        sortie = charger()
        self.assertEqual(Membre.objects.count(), NOMBRE_PAR_DEFAUT)
        self.assertIn(f"0 faux membres supprimés, {NOMBRE_PAR_DEFAUT} créés", sortie)

    def test_le_nombre_se_choisit(self):
        charger("--nombre", "5")
        self.assertEqual(Membre.objects.count(), 5)

    def test_relancer_remet_la_base_dans_le_meme_etat(self):
        charger("--nombre", "20")
        avant = sorted(Membre.objects.values_list("email", "nom", "categorie"))
        formations_avant = Formation.objects.count()
        # On abîme les fausses données : un membre renommé, un autre supprimé.
        premier, second = Membre.objects.all()[:2]
        premier.nom = "Modifié"
        premier.save()
        second.delete()

        sortie = charger("--nombre", "20")

        self.assertIn("19 faux membres supprimés, 20 créés", sortie)
        self.assertEqual(sorted(Membre.objects.values_list("email", "nom", "categorie")), avant)
        self.assertEqual(Formation.objects.count(), formations_avant)

    def test_les_comptes_crees_a_la_main_ne_sont_jamais_touches(self):
        Membre.objects.create_superuser(
            "admin@exemple.test", "motdepasse-de-test", prenom="Admin", nom="Exemple"
        )
        Membre.objects.create_user(
            "ines.martin@exemple.test", "motdepasse-de-test", prenom="Inès", nom="Martin"
        )
        charger("--nombre", "5")
        charger("--nombre", "5")
        self.assertTrue(Membre.objects.filter(email="admin@exemple.test").exists())
        self.assertTrue(Membre.objects.filter(email="ines.martin@exemple.test").exists())
        self.assertEqual(Membre.objects.count(), 5 + 2)

    def test_les_faux_membres_sont_valides_et_ont_le_mot_de_passe_commun(self):
        charger("--nombre", "20")
        for membre in Membre.objects.all():
            membre.full_clean(exclude=["password"])  # respecte toutes les règles du modèle
            self.assertEqual(membre.statut_inscription, Membre.StatutInscription.VALIDEE)
            self.assertFalse(membre.is_staff)
        un_membre = Membre.objects.first()
        self.assertEqual(
            authenticate(email=un_membre.email, password="motdepasse-factice"), un_membre
        )

    def test_les_referentiels_sont_deja_la_grace_a_la_migration(self):
        charger("--nombre", "1")
        self.assertEqual(Diplome.objects.count(), 20)

    def test_chaque_alumni_a_son_parcours(self):
        charger("--nombre", "50")
        for membre in Membre.objects.filter(categorie="alumni").prefetch_related("formations"):
            self.assertIn(membre.formations.count(), (1, 2))

    @override_settings(DEBUG=False)
    def test_refuse_de_tourner_hors_developpement(self):
        with self.assertRaises(CommandError):
            charger("--nombre", "1")
        self.assertEqual(Membre.objects.count(), 0)
