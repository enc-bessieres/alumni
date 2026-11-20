"""Vérifie que Pillow est installé et que Django contrôle bien les images envoyées.

Voir docs/decisions/0003-images-pillow.md.
"""

from io import BytesIO

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image


class FormulaireImage(forms.Form):
    image = forms.ImageField()


def fichier_png():
    tampon = BytesIO()
    Image.new("RGB", (2, 2), "white").save(tampon, format="PNG")
    return SimpleUploadedFile("image.png", tampon.getvalue(), content_type="image/png")


class ImagesTests(SimpleTestCase):
    def test_une_vraie_image_est_acceptee(self):
        formulaire = FormulaireImage(files={"image": fichier_png()})

        self.assertTrue(formulaire.is_valid(), formulaire.errors)

    def test_un_fichier_qui_n_est_pas_une_image_est_refuse(self):
        faux = SimpleUploadedFile("image.png", b"pas une image", content_type="image/png")
        formulaire = FormulaireImage(files={"image": faux})

        self.assertFalse(formulaire.is_valid())
        self.assertIn("image", formulaire.errors)
