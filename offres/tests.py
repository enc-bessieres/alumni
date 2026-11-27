from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from referentiels.models import TypeDeContrat

from .models import Offre


class OffreModeleTests(TestCase):
    def test_une_offre_sans_statut_est_en_attente(self):
        contrat = TypeDeContrat.objects.create(nom="Contrat de test")
        offre = Offre.objects.create(
            titre="Développeuse web",
            organisation="Entreprise de test",
            type_de_contrat=contrat,
            lieu="Paris",
            description="<p>Description de test</p>",
            email_contact="contact@example.org",
        )
        self.assertEqual(offre.statut, Offre.Statut.EN_ATTENTE)


class OffreAdminTests(TestCase):
    def creer_membre(self, email):
        Membre = get_user_model()
        return Membre.objects.create_user(
            email=email,
            password="mot-de-passe-de-test",
            prenom="Test",
            nom="Membre",
            categorie=Membre.Categorie.ADMINISTRATIF,
            statut_inscription=Membre.StatutInscription.VALIDEE,
            is_staff=True,
        )

    def test_un_administrateur_peut_ajouter_une_offre(self):
        membre = self.creer_membre("admin@example.org")
        membre.groups.add(Group.objects.get(name="Administrateur"))
        self.client.force_login(membre)
        reponse = self.client.get(reverse("admin:offres_offre_add"))
        self.assertEqual(reponse.status_code, 200)

    def test_un_membre_sans_groupe_ne_peut_pas_ajouter_une_offre(self):
        membre = self.creer_membre("simple@example.org")
        self.client.force_login(membre)
        reponse = self.client.get(reverse("admin:offres_offre_add"))
        self.assertEqual(reponse.status_code, 403)
