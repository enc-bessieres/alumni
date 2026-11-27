import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from blog.admin import ArticleAdminForm
from blog.models import Article

DOSSIER_MEDIA_TEST = tempfile.mkdtemp()


def fichier_image(largeur=100, hauteur=100, format_="JPEG", exif=None):
    tampon = BytesIO()
    image = Image.new("RGB", (largeur, hauteur), "white")
    if exif is None:
        image.save(tampon, format=format_)
    else:
        image.save(tampon, format=format_, exif=exif)
    return SimpleUploadedFile(f"photo.{format_.lower()}", tampon.getvalue())


class FormulaireImageTests(TestCase):
    def formulaire(self, image, texte_alternatif=""):
        return ArticleAdminForm(
            data={
                "titre": "Un article",
                "slug": "un-article",
                "contenu": "<p>Texte</p>",
                "statut": Article.Statut.PUBLIE,
                "texte_alternatif": texte_alternatif,
            },
            files={"image": image},
        )

    def test_une_image_sans_texte_alternatif_est_refusee(self):
        formulaire = self.formulaire(fichier_image())
        formulaire.is_valid()
        self.assertIn("texte_alternatif", formulaire.errors)

    def test_une_image_trop_lourde_est_refusee(self):
        # Une image BMP n'est pas compressée : 1400 x 1300 pixels font plus de 5 Mo.
        formulaire = self.formulaire(fichier_image(1400, 1300, "BMP"), "Une image")
        formulaire.is_valid()
        self.assertIn("image", formulaire.errors)

    def test_l_image_envoyee_est_nettoyee(self):
        exif = Image.Exif()
        exif[0x0110] = "Mon telephone"
        formulaire = self.formulaire(fichier_image(exif=exif.tobytes()), "Une image")
        formulaire.is_valid()
        image_propre = Image.open(formulaire.cleaned_data["image"])
        self.assertEqual(len(image_propre.getexif()), 0)


@override_settings(MEDIA_ROOT=DOSSIER_MEDIA_TEST)
class AffichageImageTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(DOSSIER_MEDIA_TEST, ignore_errors=True)
        super().tearDownClass()

    def creer_article(self, **champs):
        return Article.objects.create(
            titre="Un article",
            slug="un-article",
            contenu="<p>Texte</p>",
            statut=Article.Statut.PUBLIE,
            **champs,
        )

    def test_l_image_s_affiche_avec_son_texte_alternatif(self):
        article = self.creer_article(image=fichier_image(), texte_alternatif="La cour de l'école")
        reponse = self.client.get(article.get_absolute_url())
        self.assertContains(reponse, 'alt="La cour de l&#x27;école"')

    def test_un_article_sans_image_n_affiche_pas_d_image(self):
        article = self.creer_article()
        reponse = self.client.get(article.get_absolute_url())
        self.assertNotContains(reponse, 'class="image-article"')
