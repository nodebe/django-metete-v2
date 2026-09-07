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

    # Create Surveys
    create_surveys = "Create Surveys", "create_surveys"
    update_surveys = "Update Surveys", "update_surveys"
    delete_surveys = "Delete Surveys", "delete_surveys"
    activate_or_deactivate_surveys = "Activate/Deactivate Surveys", "activate_or_deactivate_surveys"


class RoleEnum(TextChoices):
    sysadmin = "System Administrator", "sys_admin"
    client = "Client", "client"


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
    "Survey Management": [
        PermissionEnum.create_surveys,
        PermissionEnum.update_surveys,
        PermissionEnum.delete_surveys,
        PermissionEnum.activate_or_deactivate_surveys
    ]
}

DefaultRolesPermissions = {
    RoleEnum.sysadmin: [
        PermissionGroups.get("Role Management"),
        PermissionGroups.get("User Management"),
        PermissionGroups.get("Survey Management"),
    ],
    RoleEnum.client: []
}

# Hierarchy
SYSADMIN_ABOVE = []

RoleHierarchy = {
    RoleEnum.sysadmin: SYSADMIN_ABOVE
}
