"""
Back-office des référentiels.

Les droits sont ceux de Django (règle 3 : un seul endroit, le mécanisme du framework) :
il faut le statut « équipe » et la permission du modèle (view/add/change/delete_diplome…) ;
le superutilisateur les a toutes.
"""

from django.contrib import admin

from .models import Diplome, Niveau, Site


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
