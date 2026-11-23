from django.contrib import admin

from .models import MotInterdit


@admin.register(MotInterdit)
class MotInterditAdmin(admin.ModelAdmin):
    list_display = ["mot", "ajoute_le"]
    search_fields = ["mot"]
