import smtplib
from unittest import mock

from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre

VALIDATION = reverse("membres:validation")
EN_ATTENTE = Membre.StatutInscription.EN_ATTENTE
VALIDEE = Membre.StatutInscription.VALIDEE
REFUSEE = Membre.StatutInscription.REFUSEE


def creer(prenom, nom, groupe=None, **champs):
    champs.setdefault("statut_inscription", VALIDEE)
    champs.setdefault("categorie", Membre.Categorie.ALUMNI)
    membre = Membre.objects.create_user(
        f"{prenom}.{nom}@exemple.test".lower(),
        "motdepasse-de-test",
        prenom=prenom,
        nom=nom,
        **champs,
    )
    if groupe:
        # Les groupes et leurs permissions viennent de membres/droits.py (créés à chaque migrate).
        membre.groups.add(Group.objects.get(name=groupe))
    return membre


def decider(membre):
    return reverse("membres:decider", args=[membre.pk])


class AccesValidationTests(TestCase):
    def test_un_visiteur_est_renvoye_vers_la_connexion(self):
        reponse = self.client.get(VALIDATION)

        self.assertEqual(reponse.status_code, 302)
        self.assertIn("/compte/login/", reponse["Location"])

    def test_un_membre_sans_le_droit_recoit_une_403(self):
        self.client.force_login(creer("Ines", "Membre"))
        attente = creer("Paul", "Attente", statut_inscription=EN_ATTENTE)

        self.assertEqual(self.client.get(VALIDATION).status_code, 403)
        reponse = self.client.post(decider(attente), {"decision": "valider"})
        self.assertEqual(reponse.status_code, 403)
        attente.refresh_from_db()
        self.assertEqual(attente.statut_inscription, EN_ATTENTE)

    def test_validateur_et_administrateur_y_ont_acces(self):
        for groupe in ("Validateur", "Administrateur"):
            with self.subTest(groupe=groupe):
                self.client.force_login(creer("Vic", groupe, groupe=groupe))
                self.assertEqual(self.client.get(VALIDATION).status_code, 200)


class ValidationTests(TestCase):
    def setUp(self):
        self.client.force_login(creer("Vic", "Validateur", groupe="Validateur"))
        self.lea = creer("Lea", "Martin", statut_inscription=EN_ATTENTE)
        EmailAddress.objects.create(user=self.lea, email=self.lea.email, verified=True)

    def test_liste_les_inscriptions_en_attente_seulement(self):
        creer("Hugo", "Valide")
        creer("Rita", "Refus", statut_inscription=REFUSEE)

        reponse = self.client.get(VALIDATION)

        self.assertEqual(list(reponse.context["membres"]), [self.lea])
        self.assertContains(reponse, "lea.martin@exemple.test")
        self.assertContains(reponse, "1 inscription en attente")

    def test_valider_ouvre_l_annuaire_et_previent_le_membre(self):
        reponse = self.client.post(decider(self.lea), {"decision": "valider"}, follow=True)

        self.lea.refresh_from_db()
        self.assertEqual(self.lea.statut_inscription, VALIDEE)
        self.assertContains(reponse, "Inscription de Lea Martin validée")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["lea.martin@exemple.test"])
        self.assertIn("validée", mail.outbox[0].subject)
        self.assertIn("http://testserver/annuaire/", mail.outbox[0].body)
        # Le membre validé voit maintenant l'annuaire.
        self.client.force_login(self.lea)
        self.assertEqual(self.client.get(reverse("membres:annuaire")).status_code, 200)

    def test_refuser_ferme_le_compte_et_previent_le_membre(self):
        self.client.post(decider(self.lea), {"decision": "refuser"})

        self.lea.refresh_from_db()
        self.assertEqual(self.lea.statut_inscription, REFUSEE)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("n'a pas été retenue", mail.outbox[0].body)

    def test_si_l_e_mail_ne_part_pas_la_decision_reste_et_le_validateur_est_prevenu(self):
        with mock.patch(
            "membres.validation.send_mail", side_effect=smtplib.SMTPException("en panne")
        ):
            reponse = self.client.post(decider(self.lea), {"decision": "valider"}, follow=True)

        self.lea.refresh_from_db()
        self.assertEqual(self.lea.statut_inscription, VALIDEE)
        self.assertContains(reponse, "l&#x27;e-mail n&#x27;a pas pu partir")

    def test_une_inscription_deja_traitee_ne_change_plus(self):
        # Un autre validateur a refusé entre-temps : pas de retour en arrière, pas d'e-mail.
        Membre.objects.filter(pk=self.lea.pk).update(statut_inscription=REFUSEE)

        reponse = self.client.post(decider(self.lea), {"decision": "valider"}, follow=True)

        self.lea.refresh_from_db()
        self.assertEqual(self.lea.statut_inscription, REFUSEE)
        self.assertContains(reponse, "déjà été traitée")
        self.assertEqual(mail.outbox, [])

    def test_une_decision_inconnue_ne_change_rien(self):
        self.client.post(decider(self.lea), {"decision": "supprimer"})

        self.lea.refresh_from_db()
        self.assertEqual(self.lea.statut_inscription, EN_ATTENTE)
        self.assertEqual(mail.outbox, [])

    def test_on_ne_decide_qu_en_post(self):
        self.assertEqual(self.client.get(decider(self.lea)).status_code, 405)
