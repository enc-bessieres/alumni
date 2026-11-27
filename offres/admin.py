from django.contrib import admin

from .models import Offre


@admin.register(Offre)
class OffreAdmin(admin.ModelAdmin):
    list_display = ["titre", "organisation", "type_de_contrat", "statut", "creee_le"]
    list_filter = ["statut", "type_de_contrat"]
    search_fields = ["titre", "organisation"]
    list_select_related = ["type_de_contrat"]
