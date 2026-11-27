"""Les pages provisoires réservées aux membres connectés (règle 3)."""

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

# Pages provisoires qui exigent la connexion, même tant qu'elles sont vides.
PAGES_PRIVEES = ["profil"]  # « Paramètres » est la vraie page de membres/ (testée là-bas)


class PagesPriveesTests(TestCase):
    def test_un_visiteur_non_connecte_est_redirige_vers_la_connexion(self):
        # resolve_url suit LOGIN_URL : le test reste juste si l'adresse de connexion change.
        connexion = resolve_url(settings.LOGIN_URL)
        for nom in PAGES_PRIVEES:
            with self.subTest(page=nom):
                adresse = reverse(f"gabarit:{nom}")

                reponse = self.client.get(adresse)

                self.assertRedirects(
                    reponse, f"{connexion}?next={adresse}", fetch_redirect_response=False
                )
