from django import forms
from django.contrib import admin
from django.core.files.uploadedfile import UploadedFile

from images.outils import nettoyer_image, verifier_taille

from .models import Article


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "titre",
            "slug",
            "resume",
            "contenu",
            "image",
            "texte_alternatif",
            "auteur",
            "statut",
            "publie_le",
        ]

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if isinstance(image, UploadedFile):
            verifier_taille(image)
            return nettoyer_image(image)
        return image

    def clean(self):
        donnees = super().clean()
        if donnees.get("image") and not donnees.get("texte_alternatif"):
            self.add_error("texte_alternatif", "Décrivez l'image en une phrase.")
        return donnees


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["titre", "slug", "statut"]
    list_filter = ["statut"]
    search_fields = ["titre", "contenu"]
    prepopulated_fields = {"slug": ["titre"]}
    autocomplete_fields = ["auteur"]
    form = ArticleAdminForm

    def save_model(self, request, obj, form, change):
        if obj.auteur is None:
            obj.auteur = request.user
        super().save_model(request, obj, form, change)
