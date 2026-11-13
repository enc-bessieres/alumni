"""
Back-office des référentiels.

Les droits sont ceux de Django (règle 3 : un seul endroit, le mécanisme du framework) :
il faut le statut « équipe » et la permission du modèle (view/add/change/delete_diplome…) ;
le superutilisateur les a toutes.
"""

from django.contrib import admin

from .models import Diplome, Formation, Niveau, Site


@admin.register(Site, Niveau)
class ReferentielAdmin(admin.ModelAdmin):
    list_display = ["nom"]
    search_fields = ["nom"]
    readonly_fields = ["legacy_id"]  # affiché, jamais modifiable


@admin.register(Diplome)
class DiplomeAdmin(admin.ModelAdmin):
    list_display = ["nom", "niveau"]
    list_filter = ["niveau"]
    search_fields = ["nom"]
    readonly_fields = ["legacy_id"]


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ["membre", "diplome", "site", "promo"]
    list_filter = ["diplome__niveau", "diplome", "site", "promo"]
    search_fields = ["membre__nom", "membre__prenom", "membre__email"]
    # Une liste déroulante de 1300 membres serait inutilisable : un champ avec une loupe
    # ouvre la liste des membres pour en choisir un. (autocomplete_fields demanderait
    # l'admin du Membre, qui arrive avec la branche alex/9-droits.)
    raw_id_fields = ["membre"]
    readonly_fields = ["legacy_id"]
