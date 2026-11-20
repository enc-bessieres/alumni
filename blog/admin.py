from django.contrib import admin

from .models import Article


@admin.action(description="Publier les articles sélectionnés")
def publier(modeladmin, request, queryset):
    for article in queryset:
        article.statut = Article.Statut.PUBLIE
        article.save()


@admin.action(description="Refuser les articles sélectionnés")
def refuser(modeladmin, request, queryset):
    for article in queryset:
        article.statut = Article.Statut.REFUSE
        article.save()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["titre", "slug", "statut"]
    list_filter = ["statut"]
    search_fields = ["titre", "contenu"]
    prepopulated_fields = {"slug": ["titre"]}
    actions = [publier, refuser]
