from django.contrib.auth.mixins import AccessMixin
from utils.errors import PermissionDeniedError, NotAuthorizedError


class AppAccessMixin(AccessMixin):
    def handle_no_permission(self):
        raise PermissionDeniedError()


class ActiveUserPermission(AppAccessMixin):

    def has_permission(self):
        if not self.request.user.is_anonymous and self.request.user.deactivated_at is None:
            return True

        return False

    def check_required_roles_and_permissions(self):
        if not self.has_permission():
            return self.handle_no_permission()

        return None


class CustomApiPermissionRequired(AppAccessMixin):
    """Verify that the current user has all specified permissions."""
    roles_required = None
    permission_required = None
    any_of_permission = None
    user_type_required = None

    def get_permission_required(self):
        if self.permission_required:
            return self.permission_required

        return self.any_of_permission

    def has_permission(self):
        perms = self.get_permission_required()
        if not perms:
            return True

        return self.check_permission_list(self.request.user, perms)

    def has_roles(self):
        roles = self.roles_required
        if not roles:
            return True

        return self.check_role_list(self.request.user, roles)

    def check_permission_list(self, user, perms_list):
        if user.is_anonymous:
            raise NotAuthorizedError()

        if not user.is_anonymous and user.deactivated_at is not None:
            return False

        if not isinstance(perms_list, list):
            perms_list = [perms_list]

        for perm in perms_list:
            if user.has_permission(perm):
                return True

        return False

    def check_role_list(self, user, role_list):
        if not isinstance(role_list, list):
            role_list = [role_list]

        return user.has_any_of_roles(role_list)

    def check_required_roles_and_permissions(self):
        if not self.has_permission():
            return self.handle_no_permission()

        if not self.has_roles():
            return self.handle_no_permission()
        return None

    def check_permission_in_service(self, permissions_list):
        return self.check_permission_list(self.request.user, permissions_list)
