from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("ecrire/", views.ecrire, name="ecrire"),
    path("<slug:slug>/", views.detail, name="detail"),
    path("<slug:slug>/signaler/", views.signaler, name="signaler"),
]
