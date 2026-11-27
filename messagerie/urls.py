from django.urls import path

from . import views

app_name = "messagerie"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("<int:pk>/", views.conversation, name="conversation"),
    path("ecrire/<int:pk>/", views.ecrire, name="ecrire"),
]
