from django.urls import path

from . import views

app_name = "mentorat"

urlpatterns = [
    path("mes-preferences/", views.mes_preferences, name="mes_preferences"),
]
