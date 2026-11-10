from django.apps import AppConfig
from django.db.models.signals import post_migrate, post_save


class MembresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "membres"
    verbose_name = "Membres"

    def ready(self):
        # Branche les droits de membres/droits.py sur les événements de Django.
        from . import droits
        from .models import Membre

        post_migrate.connect(droits.creer_groupes, dispatch_uid="creer_groupes")
        post_save.connect(droits.appliquer_groupes, sender=Membre, dispatch_uid="appliquer_groupes")
