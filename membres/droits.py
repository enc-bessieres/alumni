from django.contrib.auth.models import Group, Permission


def assurer_droits_evenements():
    groupe_admin, _ = Group.objects.get_or_create(name="Administrateur")
    codes_permissions = [
        "add_evenement",
        "change_evenement",
        "delete_evenement",
        "view_evenement",
    ]
    permissions = Permission.objects.filter(
        content_type__app_label="evenements",
        codename__in=codes_permissions,
    )
    groupe_admin.permissions.add(*permissions)
    return groupe_admin