"""
Mot de passe oublié, fourni par django-allauth.
Le même lien active les comptes importés de Datalumni qui n'ont jamais eu de mot de passe.
En test, Django garde les e-mails en mémoire (mail.outbox) au lieu de les envoyer.
"""

import re
from datetime import datetime, timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase

from membres.tests.test_connexion import creer_membre, se_connecter

NOUVEAU = "Un-nouveau-mot-de-passe-2026"


class MotDePasseOublieTests(TestCase):
    def demander_un_lien(self, email):
        self.client.post("/compte/password/reset/", {"email": email})

    def lien_recu(self):
        return re.search(r"/compte/password/reset/key/\S+/", mail.outbox[-1].body).group(0)

    def choisir_un_mot_de_passe(self, lien):
        # allauth retire la clé de l'adresse avant d'afficher le formulaire : on suit le renvoi.
        page = self.client.get(lien, follow=True)
        formulaire = page.redirect_chain[-1][0] if page.redirect_chain else lien
        return self.client.post(formulaire, {"password1": NOUVEAU, "password2": NOUVEAU})

    def test_un_membre_recoit_un_lien_par_e_mail(self):
        creer_membre("ines@exemple.test")
        self.demander_un_lien("ines@exemple.test")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ines@exemple.test"])

    def test_le_lien_permet_de_choisir_un_nouveau_mot_de_passe(self):
        creer_membre("ines@exemple.test")
        self.demander_un_lien("ines@exemple.test")
        self.choisir_un_mot_de_passe(self.lien_recu())
        self.assertRedirects(se_connecter(self.client, "ines@exemple.test", NOUVEAU), "/")

    def test_le_lien_ne_sert_qu_une_fois(self):
        creer_membre("ines@exemple.test")
        self.demander_un_lien("ines@exemple.test")
        lien = self.lien_recu()
        self.choisir_un_mot_de_passe(lien)
        reponse = self.client.get(lien, follow=True)
        self.assertNotContains(reponse, 'name="password1"')  # plus de formulaire : lien invalide

    def test_le_lien_expire_au_bout_d_une_heure(self):
        creer_membre("ines@exemple.test")
        self.demander_un_lien("ines@exemple.test")
        lien = self.lien_recu()
        dans_61_minutes = datetime.now() + timedelta(minutes=61)
        # On avance l'horloge du générateur de jetons de Django, utilisé par allauth.
        with mock.patch(
            "django.contrib.auth.tokens.PasswordResetTokenGenerator._now",
            return_value=dans_61_minutes,
        ):
            reponse = self.client.get(lien, follow=True)
        self.assertNotContains(reponse, 'name="password1"')

    def test_aucun_e_mail_pour_une_adresse_inconnue(self):
        self.demander_un_lien("inconnu@exemple.test")
        self.assertEqual(len(mail.outbox), 0)

    def test_un_compte_importe_sans_mot_de_passe_s_active_par_ce_lien(self):
        membre = creer_membre("importe@exemple.test")
        membre.set_unusable_password()
        membre.save()
        self.demander_un_lien("importe@exemple.test")
        self.choisir_un_mot_de_passe(self.lien_recu())
        self.assertRedirects(se_connecter(self.client, "importe@exemple.test", NOUVEAU), "/")
