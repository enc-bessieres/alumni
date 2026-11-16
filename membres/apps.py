from django.apps import AppConfig
from django.db.models.signals import post_migrate


class MembresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "membres"
    verbose_name = "Membres"

    def ready(self):
        # Après chaque `migrate`, crée ou met à jour les groupes définis dans membres/droits.py.
        from . import droits

        post_migrate.connect(droits.creer_groupes, dispatch_uid="creer_groupes")
