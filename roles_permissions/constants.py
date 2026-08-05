from django.db.models import TextChoices


class PermissionEnum(TextChoices):
    # Roles
    view_roles = "View Roles", "view_roles"
    create_roles = "Create Roles", "create_roles"
    update_roles = "Update Roles", "update_roles"
    delete_roles = "Delete Roles", "delete_roles"

    # Users
    view_users = "View Users", "view_users"
    create_users = "Create Users", "create_users"
    update_users = "Update Users", "update_users"
    activate_or_deactivate_users = "Activate/Deactivate Users", "activate_deactivate_users"


class RoleEnum(TextChoices):
    sysadmin = "System Administrator", "sys_admin"


PermissionGroups = {
    "Role Management": [
        PermissionEnum.view_roles,
        PermissionEnum.create_roles,
        PermissionEnum.update_roles,
        PermissionEnum.delete_roles
    ],
    "User Management": [
        PermissionEnum.create_users,
        PermissionEnum.view_users,
        PermissionEnum.update_users,
        PermissionEnum.activate_or_deactivate_users
    ],
}

DefaultRolesPermissions = {
    RoleEnum.sysadmin: [
        PermissionGroups.get("Role Management"),
        PermissionGroups.get("User Management"),
    ],
}

# Hierarchy
SYSADMIN_ABOVE = []

RoleHierarchy = {
    RoleEnum.sysadmin: SYSADMIN_ABOVE
}
