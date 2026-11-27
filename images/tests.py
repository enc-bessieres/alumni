from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from images.outils import TAILLE_MAX, nettoyer_image, verifier_taille


def fichier_image(largeur, hauteur, format_="JPEG", exif=None):
    """Fabrique une image blanche, comme si un membre l'avait envoyée."""
    tampon = BytesIO()
    image = Image.new("RGB", (largeur, hauteur), "white")
    if exif is None:
        image.save(tampon, format=format_)
    else:
        image.save(tampon, format=format_, exif=exif)
    return SimpleUploadedFile(f"photo.{format_.lower()}", tampon.getvalue())


class VerifierTailleTests(SimpleTestCase):
    def test_une_image_trop_lourde_est_refusee(self):
        fichier = SimpleUploadedFile("lourde.jpg", b"0" * (TAILLE_MAX + 1))
        with self.assertRaises(ValidationError):
            verifier_taille(fichier)

    def test_une_image_de_5_mo_pile_est_acceptee(self):
        fichier = SimpleUploadedFile("limite.jpg", b"0" * TAILLE_MAX)
        verifier_taille(fichier)


class NettoyerImageTests(SimpleTestCase):
    def test_les_exif_sont_supprimes(self):
        exif = Image.Exif()
        exif[0x0110] = "Mon telephone"
        resultat = nettoyer_image(fichier_image(100, 100, exif=exif.tobytes()))
        self.assertEqual(len(Image.open(resultat).getexif()), 0)

    def test_une_image_trop_large_est_reduite_sans_deformation(self):
        resultat = nettoyer_image(fichier_image(3200, 1000))
        self.assertEqual(Image.open(resultat).size, (1600, 500))

    def test_une_petite_image_garde_sa_taille_et_son_format(self):
        resultat = nettoyer_image(fichier_image(800, 600, format_="PNG"))
        image = Image.open(resultat)
        self.assertEqual(image.size, (800, 600))
        self.assertEqual(image.format, "PNG")
