from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["titre", "slug", "publiee", "modifiee_le"]
    list_filter = ["publiee"]
    search_fields = ["titre", "contenu"]
    prepopulated_fields = {"slug": ["titre"]}
