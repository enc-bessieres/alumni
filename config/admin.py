"""
Le back-office du projet : celui de Django, avec une seule différence (issue #12).

Par défaut, Django renvoie vers sa page de connexion toute personne qui n'a pas accès.
Ici, une personne déjà connectée mais qui n'est pas de l'équipe reçoit une erreur 403.
Les droits eux-mêmes restent ceux de Django (statut « équipe » et permissions).
"""

from functools import update_wrapper

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.urls import reverse


class SiteAdmin(admin.AdminSite):
    def admin_view(self, view, cacheable=False):
        vue = super().admin_view(view, cacheable)

        def vue_protegee(request, *args, **kwargs):
            if request.user.is_authenticated and not self.has_permission(request):
                if request.path == reverse("admin:logout", current_app=self.name):
                    return view(request, *args, **kwargs)
                raise PermissionDenied
            return vue(request, *args, **kwargs)

        return update_wrapper(vue_protegee, vue)
