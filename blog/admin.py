from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["titre", "slug", "statut"]
    list_filter = ["statut"]
    search_fields = ["titre", "contenu"]
    prepopulated_fields = {"slug": ["titre"]}
    autocomplete_fields = ["auteur"]

    def save_model(self, request, obj, form, change):
        if obj.auteur is None:
            obj.auteur = request.user
        super().save_model(request, obj, form, change)
