from django.test import SimpleTestCase

from .champs import nettoyer


class NettoyerTests(SimpleTestCase):
    def test_supprime_le_html_dangereux(self):
        html = nettoyer(
            "<p>Bonjour</p><script>alert(1)</script>"
            '<p onclick="alert(2)">Clic</p>'
            '<p><a href="javascript:alert(3)">Piège</a></p>'
        )
        self.assertNotIn("<script", html)
        self.assertNotIn("onclick", html)
        self.assertNotIn("javascript:", html)
        self.assertIn("Bonjour", html)

    def test_garde_la_mise_en_forme_autorisee(self):
        html = nettoyer(
            '<h2>Titre</h2><p><strong>Gras</strong> <a href="https://exemple.test">lien</a></p>'
        )
        self.assertIn("<h2>Titre</h2>", html)
        self.assertIn("<strong>Gras</strong>", html)
        self.assertIn('href="https://exemple.test"', html)
