from django.contrib import admin

from .models import Evenement


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ("titre", "date_debut", "date_fin", "lieu", "publie")
    list_filter = ("publie", "date_debut")
    search_fields = ("titre", "lieu")
    date_hierarchy = "date_debut"
