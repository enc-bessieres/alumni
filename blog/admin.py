from django.contrib import admin

from .models import Article

@admin.action(description="Retirer les articles sélectionnés du site")
def retirer(modeladmin, request, queryset):
    for article in queryset:
        article.statut = Article.Statut.REFUSE
        article.save()
        modeladmin.log_change(request, article, "Article retiré du site.")

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["titre", "slug", "statut"]
    list_filter = ["statut"]
    search_fields = ["titre", "contenu"]
    prepopulated_fields = {"slug": ["titre"]}
    autocomplete_fields = ["auteur"]
    actions = [retirer]

    def save_model(self, request, obj, form, change):
        if obj.auteur is None:
            obj.auteur = request.user
        super().save_model(request, obj, form, change)
