from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Article, Signalement


@admin.action(description="Retirer les articles sélectionnés du site")
def retirer(modeladmin, request, queryset):
    for article in queryset:
        article.statut = Article.Statut.REFUSE
        article.save()
        modeladmin.log_change(request, article, "Article retiré du site.")


@admin.action(description="Retirer les articles signalés")
def retirer_articles_signales(modeladmin, request, queryset):
    articles = Article.objects.filter(signalements__in=queryset).distinct()
    retirer(modeladmin, request, articles)
    queryset.update(traite=True)


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


@admin.action(description="Marquer comme traités")
def marquer_traites(modeladmin, request, queryset):
    queryset.update(traite=True)


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ["lien_article", "nombre", "membre", "motif", "traite", "cree_le"]
    list_display_links = ["cree_le"]
    list_filter = ["traite"]
    readonly_fields = ["article", "membre", "motif", "cree_le"]

    @admin.display(description="article", ordering="article__titre")
    def lien_article(self, signalement):
        adresse = reverse("admin:blog_article_change", args=[signalement.article.pk])
        return format_html('<a href="{}" target="_blank">{}</a>', adresse, signalement.article)

    def get_queryset(self, request):
        return Signalement.objects.annotate(nb_signalements=Count("article__signalements"))

    def get_ordering(self, request):
        return ["-nb_signalements", "-cree_le"]

    @admin.display(description="signalements sur l'article", ordering="nb_signalements")
    def nombre(self, signalement):
        return signalement.nb_signalements
