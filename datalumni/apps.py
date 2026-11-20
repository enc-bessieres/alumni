from django.apps import AppConfig


class DatalumniConfig(AppConfig):
    """La migration depuis Datalumni : export factice, puis import (issues #36 à #38)."""

    name = "datalumni"
    verbose_name = "Migration Datalumni"
