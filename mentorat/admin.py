# Droits : permissions du groupe Administrateur, dans membres/droits.py (règle 3).
from django.contrib import admin

from .models import ProfilMentorat, Sujet


@admin.register(Sujet)
class SujetAdmin(admin.ModelAdmin):
    list_display = ["nom"]
    search_fields = ["nom"]


@admin.register(ProfilMentorat)
class ProfilMentoratAdmin(admin.ModelAdmin):
    list_display = ["membre", "role", "nb_max_mentores", "modifie_le"]
    list_filter = ["role", "sujets"]
    search_fields = ["membre__nom", "membre__prenom", "membre__email"]
    autocomplete_fields = ["membre"]
    filter_horizontal = ["sujets"]
