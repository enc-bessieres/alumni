from django.contrib import admin

from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
        list_display = ["titre", "slug", "statut" ]
        list_filter = ["statut"]
        search_fields = ["titre", "contenu"]
        prepopulated_fields = {"slug": ["titre"]}