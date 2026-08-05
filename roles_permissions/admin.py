from django.contrib import admin
from base.admin import BaseAdmin
from roles_permissions.models import Role, Permission


@admin.register(Role)
class RoleAdmin(BaseAdmin):
    list_display = ["name", "label", "created_at", "is_default", "is_private"]

    # def has_add_permission(self, request):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False


@admin.register(Permission)
class PermissionAdmin(BaseAdmin):
    list_display = ["name", "label"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
