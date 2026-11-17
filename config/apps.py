from django.contrib.admin.apps import AdminConfig


class AdminDuProjet(AdminConfig):
    """Remplace le back-office par défaut de Django par celui de config/admin.py."""

    default_site = "config.admin.SiteAdmin"
