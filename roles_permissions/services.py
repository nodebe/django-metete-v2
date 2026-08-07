from django.db.models import Q
from utils.constants import ErrorMessages
from utils.errors import PermissionDeniedError
from utils.service import CustomApiRequestProcessorBase
from .constants import PermissionGroups, DefaultRolesPermissions, RoleHierarchy, RoleEnum
from .models import Permission, Role


class PermissionService(CustomApiRequestProcessorBase):
    def __init__(self, request):
        from roles_permissions.serializers import PermissionSerializer
        super().__init__(request)
        self.serializer_class = PermissionSerializer

    @staticmethod
    def create_default_permissions():
        permission_ids = []
        for group, permissions in PermissionGroups.items():
            for permission in permissions:
                permission_name = permission.value
                permission_label = permission.label

                permission_obj, is_created = Permission.objects.update_or_create(
                    label=permission_label,
                    defaults={
                        "group_name": group,
                        "name": permission_name,
                    }
                )
                permission_ids.append(permission_obj.pk)
                print(f"Permission '{permission_obj}'", "created" if is_created else "updated")

        Permission.objects.exclude(pk__in=permission_ids).delete()

    @classmethod
    def get_permissions_by_ids(cls, permission_ids):
        if isinstance(permission_ids, str):
            permission_ids = [permission_ids]
        return Permission.objects.filter(pk__in=permission_ids)

    @classmethod
    def get_permissions_by_names(cls, permission_names):
        if isinstance(permission_names, str):
            permission_names = [permission_names]
        return Permission.objects.filter(name__in=permission_names)

    @classmethod
    def get_permission_by_id(cls, permission_id):
        return Permission.objects.filter(pk=permission_id)

    @classmethod
    def get_permission_by_name(cls, permission_name):
        return Permission.objects.filter(name=permission_name)

    def fetch_list(self, filter_params, **kwargs):
        filter_keyword = filter_params.get("keyword")

        q = Q()
        if filter_keyword:
            q = Q(name__icontains=filter_keyword)

        queryset = Permission.objects.filter(q).order_by("name")

        return queryset


class RoleService(CustomApiRequestProcessorBase):

    def __init__(self, request=None):
        from roles_permissions.serializers import RoleSerializer
        super().__init__(request)
        self.serializer_class = RoleSerializer

    @staticmethod
    def create_default_roles():
        permission_service = PermissionService(None)

        for key, value in DefaultRolesPermissions.items():
            role = key
            role_name = role.value
            role_label = role.label

            permission_groups = value

            role, is_created = Role.objects.update_or_create(
                label=role_label,
                defaults={
                    "name": role_name,
                    "description": role_name
                }
            )

            role.permissions.clear()

            for permission in permission_groups:
                if not isinstance(permission, list):
                    permission = [permission]

                role_permissions = permission_service.get_permissions_by_names(permission)
                role.permissions.add(*role_permissions)
                role.save()

            print("Permissions added for role '{}'".format(role_name))

    def create(self, payload):
        permission_service = PermissionService(self.request)
        permissions = permission_service.get_permissions_by_ids(payload.get("permission_ids"))

        name = payload.get("name")
        description = payload.get("description")
        user_can_be_created_by = payload.get("user_can_be_created_by")

        role, is_created = Role.objects.get_or_create(
            name=name,
            defaults={
                "description": description,
                "user_can_be_created_by": user_can_be_created_by,
                "is_default": False,
                "is_private": False
            }
        )

        if not is_created:
            return None, self.make_400(ErrorMessages.role_already_exists.format(name))

        role.permissions.add(*permissions)
        role.save()

        self.report_activity("create", role)

        return role, None

    def check_if_role_exists(self, new_role_name, existing_role_id):
        return Role.objects.filter(name=new_role_name).exclude(id=existing_role_id).exists()

    def fetch_single_by_label(self, role_label, is_private=True):
        def fetch():
            role = Role.available_objects.prefetch_related("permissions").filter(label=role_label, is_private=is_private).first()

            if not role:
                return None, self.make_404(ErrorMessages.role_not_found)

            return role, None

        cache_key = self.generate_cache_key(role_label, model=Role)
        return self.get_cache_value_or_default(cache_key, fetch)

    @classmethod
    def fetch_by_ids(cls, role_ids):
        return Role.available_objects.filter(pk__in=role_ids, is_private=False)

    def fetch_by_names(self, role_names):
        return Role.available_objects.filter(name__in=role_names, is_private=False)

    def fetch_list(self, filter_params, **kwargs):
        filter_keyword = filter_params.get("keyword")

        q = Q()

        if filter_keyword:
            q = Q(name__icontains=filter_keyword) | Q(description__icontains=filter_keyword)

        queryset = Role.available_objects.prefetch_related("permissions").filter(q).order_by("name")

        return queryset

    def merge_user_roles_below_hierarchy(self):
        roles, _ = self.get_user_role_names(self.auth_user)

        role_hierarchy_list = []

        for role in roles:
            roles_below = RoleHierarchy.get(role)
            if roles_below:
                role_hierarchy_list = role_hierarchy_list + roles_below

        # Fetch the new roles from DB that can be created by this user
        role_ids, _ = self.get_user_role_ids(self.auth_user)
        new_roles = (Role.active_available_objects.filter(user_can_be_created_by__icontains=role_ids)
                     .values_list("name", flat=True))

        role_hierarchy_list.extend(new_roles)

        return list(set(role_hierarchy_list))

    def get_user_role_names(self, user):
        def __do_get_role_names():
            roles = list(user.roles.values_list("name", flat=True))
            return roles, None

        cache_key = self.generate_cache_key("role_names", user.user_id)
        return self.get_cache_value_or_default(cache_key, __do_get_role_names)

    def get_user_permission_names(self, user):
        def __do_get_permission_names():
            if user.is_superuser or user.roles.filter(name__exact=RoleEnum.sysadmin).exists():
                permissions = Permission.objects.values_list("name", flat=True)
            else:
                permissions = Permission.objects.order_by("name").filter(
                    role__id__in=user.roles.values_list("pk", flat=True)
                ).values_list("name", flat=True).distinct()
            return list(permissions), None

        cache_key = self.generate_cache_key("permission_names", user.user_id)
        return self.get_cache_value_or_default(cache_key, __do_get_permission_names)

    def get_user_role_ids(self, user):
        def __do_get_role_ids():
            roles = list(user.roles.values_list("id", flat=True))
            return roles, None

        cache_key = self.generate_cache_key("role_ids", user.user_id)
        return self.get_cache_value_or_default(cache_key, __do_get_role_ids)

    def check_permission_to_act_based_on_role_hierarchy(self, roles):
        roles_hierarchy_list = self.merge_user_roles_below_hierarchy()

        for role in roles:
            if role.name not in roles_hierarchy_list:
                raise PermissionDeniedError(ErrorMessages.no_permission_to_assign_role.format(role))
