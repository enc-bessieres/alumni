from django.urls import path

from . import views

app_name = "pages_libres"

urlpatterns = [
    path("<slug:slug>/", views.detail, name="detail"),
]
