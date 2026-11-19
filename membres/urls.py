from django.urls import path

from . import views

app_name = "membres"

urlpatterns = [
    path("", views.annuaire, name="annuaire"),
]
