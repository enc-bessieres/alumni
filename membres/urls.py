from django.urls import path

from . import validation, views

app_name = "membres"

urlpatterns = [
    path("annuaire/", views.annuaire, name="annuaire"),
    path("parametres/", views.parametres, name="parametres"),
]

# Page des validateurs (#89). Ajoutée à part, pour ne pas toucher aux lignes de la liste
# ci-dessus que d'autres PR modifient.
urlpatterns += [
    path("validation/", validation.inscriptions_en_attente, name="validation"),
    path("validation/<int:pk>/", validation.decider, name="decider"),
]
