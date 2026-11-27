"""
La messagerie privée. Membres et messages inventés (règle 1).
"""

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from membres.models import Membre

from .models import Conversation, Message

LISTE = reverse("messagerie:liste")


def creer_membre(prenom, visible=True, statut=Membre.StatutInscription.VALIDEE):
    return Membre.objects.create_user(
        f"{prenom.lower()}@exemple.test",
        "motdepasse-de-test",
        prenom=prenom,
        nom="Test",
        categorie=Membre.Categorie.ALUMNI,
        statut_inscription=statut,
        visible_dans_annuaire=visible,
    )


def conversation_entre(*membres, textes=("Bonjour",)):
    conversation = Conversation.objects.create()
    conversation.participants.add(*membres)
    for texte in textes:
        Message.objects.create(conversation=conversation, auteur=membres[0], texte=texte)
    return conversation


class MessagerieTests(TestCase):
    def setUp(self):
        self.ines = creer_membre("Ines")
        self.bruno = creer_membre("Bruno")
        self.chloe = creer_membre("Chloe")
        self.client.force_login(self.ines)

    def test_un_visiteur_non_connecte_est_renvoye_vers_la_connexion(self):
        self.client.logout()

        reponse = self.client.get(LISTE)

        connexion = resolve_url(settings.LOGIN_URL)
        self.assertRedirects(reponse, f"{connexion}?next={LISTE}", fetch_redirect_response=False)

    def test_un_membre_pas_encore_valide_n_y_a_pas_acces(self):
        self.client.force_login(creer_membre("Noe", statut=Membre.StatutInscription.EN_ATTENTE))

        reponse = self.client.get(LISTE)

        self.assertEqual(reponse.status_code, 403)

    def test_la_liste_ne_montre_que_ses_conversations(self):
        conversation_entre(self.ines, self.bruno, textes=["Salut Bruno"])
        conversation_entre(self.bruno, self.chloe, textes=["Message privé"])

        reponse = self.client.get(LISTE)

        self.assertContains(reponse, "Salut Bruno")
        self.assertNotContains(reponse, "Message privé")

    def test_la_conversation_d_un_autre_donne_une_404(self):
        autre = conversation_entre(self.bruno, self.chloe)

        reponse = self.client.get(autre.get_absolute_url())

        self.assertEqual(reponse.status_code, 404)

    def test_on_repond_dans_une_conversation(self):
        conversation = conversation_entre(self.ines, self.bruno)

        reponse = self.client.post(conversation.get_absolute_url(), {"texte": "Merci !"})

        self.assertRedirects(reponse, conversation.get_absolute_url())
        dernier = conversation.messages.last()
        self.assertEqual((dernier.auteur, dernier.texte), (self.ines, "Merci !"))

    def test_on_ne_peut_pas_ecrire_dans_la_conversation_d_un_autre(self):
        autre = conversation_entre(self.bruno, self.chloe)

        self.client.post(autre.get_absolute_url(), {"texte": "Intrus"})

        self.assertFalse(Message.objects.filter(texte="Intrus").exists())

    def test_ecrire_a_un_membre_cree_la_conversation(self):
        adresse = reverse("messagerie:ecrire", args=[self.bruno.pk])

        reponse = self.client.post(adresse, {"texte": "Bonjour Bruno"})

        conversation = Conversation.entre(self.ines, self.bruno)
        self.assertRedirects(reponse, conversation.get_absolute_url())
        self.assertEqual(conversation.messages.get().texte, "Bonjour Bruno")

    def test_ecrire_a_un_membre_reprend_la_conversation_existante(self):
        existante = conversation_entre(self.ines, self.bruno)

        reponse = self.client.get(reverse("messagerie:ecrire", args=[self.bruno.pk]))

        self.assertRedirects(reponse, existante.get_absolute_url())
        self.assertEqual(Conversation.objects.count(), 1)

    def test_on_n_ecrit_qu_aux_membres_de_l_annuaire(self):
        cache = creer_membre("Camille", visible=False)
        for destinataire in (cache, self.ines):  # absent de l'annuaire, puis soi-même
            with self.subTest(destinataire=destinataire.prenom):
                adresse = reverse("messagerie:ecrire", args=[destinataire.pk])

                reponse = self.client.post(adresse, {"texte": "Bonjour"})

                self.assertEqual(reponse.status_code, 404)
        self.assertFalse(Conversation.objects.exists())

    def test_un_message_vide_n_est_pas_envoye(self):
        conversation = conversation_entre(self.ines, self.bruno)

        reponse = self.client.post(conversation.get_absolute_url(), {"texte": "   "})

        self.assertEqual(reponse.status_code, 200)  # le formulaire est réaffiché
        self.assertEqual(conversation.messages.count(), 1)
