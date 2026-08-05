from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from account.models.user import User
from location.v1.models import Location
from location.v1.serializers import LocationSerializer
from roles_permissions.services import RoleService
from utils.constants import ResponseMessages, ErrorMessages
from utils.models import ModelService
from utils.service import CustomApiRequestProcessorBase, get_unique_id


class AccountService(CustomApiRequestProcessorBase):
    def __init__(self, request):
        super().__init__(request)
        self.model_service = ModelService(self.request)

    def fetch(self):
        return self.auth_user, None

    def check_email_exists(self, email):
        user = User.objects.filter(Q(email__iexact=email))

        return user.exists(), user.first()

    def check_phone_number_exists(self, phone_number):
        user = User.objects.filter(Q(phone_number__iexact=phone_number))

        return user.exists(), user.first()

    def set_profile_photo(self, profile_photo_media, user):
        user.profile_photo = profile_photo_media
        user.save(update_fields=['profile_photo'])

    def set_address(self, address, user):
        if user.address:
            self.model_service.update_model_instance(user.address, **address)
        else:
            address, error = self.model_service.create_model_instance(model=Location, payload=address)
            if error:
                return None, error

            user.address = address
            user.save(update_fields=['address'])

        return True, None

    def update(self, payload, current_user=None):
        """current_user is the user who is being acted upon"""

        if current_user is None:
            current_user = self.auth_user

        profile_photo = payload.pop("profile_photo", None)
        address = payload.pop("address", None)
        username = payload.get("username", None)
        phone_number = payload.get("phone_number", None)

        if username:
            user = self.check_username_exists(username)

            if user and user != current_user:
                return None, self.make_400(ErrorMessages.username_already_exists)

        if phone_number:
            is_exists, user = self.check_phone_number_exists(phone_number)

            if is_exists and user != current_user:
                return None, self.make_400(ErrorMessages.phone_already_exist)

        user_update, error = self.model_service.update_model_instance(model_instance=current_user, **payload)
        if error:
            return None, error

        if profile_photo:
            self.set_profile_photo(profile_photo, current_user)

        if address:
            _, error = self.set_address(address, current_user)
            if error:
                return None, error

        cache_key = self.generate_cache_key(current_user.user_id, model=User)
        self.clear_cache(cache_key)

        self.report_activity(user=current_user, description="Account Profile updated successfully")

        return user_update, None

    def fetch_user_by_user_id(self, user_id, is_background=False):
        def __do_fetch_single():
            try:
                user = User.objects.get(user_id=user_id)
                return user, None

            except User.DoesNotExist:
                if is_background:
                    return None, None

                return None, self.make_404(ErrorMessages.user_with_id_not_found.format(user_id))

            except Exception as e:
                return None, self.make_500(e, self)

        if is_background:
            return __do_fetch_single()

        cache_key = self.generate_cache_key(user_id, model=User)
        return self.get_cache_value_or_default(cache_key, __do_fetch_single)

    def fetch_user_by_phone_number(self, phone_number, is_fresh=False):
        """
        is_fresh: True for when you're searching for a signup, to allow you to continue with the flow instead of
        raising error
        """

        def __do_fetch_single():
            try:
                user = User.objects.get(phone_number=phone_number)
                return user, None

            except User.DoesNotExist:
                if is_fresh:
                    return None, None

                return None, self.make_404(ErrorMessages.user_with_phone_number_not_found.format(phone_number))

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key(phone_number, model=User)
        return self.get_cache_value_or_default(cache_key, __do_fetch_single)

    def check_username_exists(self, username):
        user = User.objects.filter(Q(username__iexact=username))

        return user.first()

    def fetch_user_data(self):
        user_data = self.get_user_data(self.auth_user)

        poppable_data = ["refresh_token", "access_token", "token_type"]
        for key in poppable_data:
            user_data.pop(key, None)

        return user_data, None

    def delete(self):
        self.auth_user.delete()
        return ResponseMessages.account_deleted_successfully, None

    def get_user_data(self, user):
        role_service = RoleService(self.request)

        roles, _ = role_service.get_user_role_names(user)
        permissions, _ = role_service.get_user_permission_names(user)
        address = LocationSerializer(user.address).data

        return {
            **user.tokens,
            "token_type": "Bearer",
            "redirect_to_2fa": False,
            "user": {
                "id": user.user_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_photo": user.profile_photo.url if user.profile_photo else None,
                "roles": roles,
                "permissions": permissions,
                "address": address
            }
        }

    def reset_password(self, payload):
        user = self.auth_user
        old_password = payload.get("old_password")
        new_password = payload.get("new_password")

        if not check_password(old_password, user.password):
            return None, self.make_400(ErrorMessages.incorrect_password)

        user.password = new_password
        user.save(update_fields=["password"])

        self.report_activity(user=user, description="Password reset successful")

        return ResponseMessages.successful_password_change, None


class UserService(CustomApiRequestProcessorBase):
    def __init__(self, request):
        from account.v1.serializers.profile import SimpleProfileSerializer

        super().__init__(request)
        self.serializer_class = SimpleProfileSerializer
        self.account_service = AccountService(self.request)
        self.role_service = RoleService(self.request)

    def create(self, payload):
        roles = payload.pop("roles", None)

        if not roles:
            return None, self.make_400(ErrorMessages.role_is_required)

        self.role_service.check_permission_to_act_based_on_role_hierarchy(roles)

        model_service = ModelService(self.request)

        payload["user_id"] = get_unique_id()

        with transaction.atomic():
            user, error = model_service.create_model_instance(model=User, payload=payload)
            if error:
                return None, error

            # Attach roles to user
            user.roles.add(*roles)

        # TODO: Send email invite

        return user, None

    def active_or_deactivate(self, payload, user_id):
        user, error = self.account_service.fetch_user_by_user_id(user_id)
        if error:
            return None, error

        status = payload.get("status", True)

        if status:
            user.is_active = True
            user.deactivated_by = None
            user.deactivated_at = None
        else:
            user.is_active = False
            user.deactivated_by = self.auth_user
            user.deactivated_at = timezone.now()

        user.save(update_fields=["is_active", "deactivated_by", "deactivated_at"])

        verb = "activated" if status else "deactivated"

        self.report_activity(activity_type=verb, data=user)

        return user, None

    def update(self, payload, user_id):
        user, error = self.account_service.fetch_user_by_user_id(user_id)
        if error:
            return None, error

        profile_photo = payload.get("profile_photo")

        if profile_photo:
            self.check_resource_owner(profile_photo, ErrorMessages.unknown_media_user)
            if hasattr(profile_photo, "owner") and profile_photo.owner != user:
                return None, self.make_400(ErrorMessages.unknown_media_user)

        roles = payload.pop("roles", None) or user.roles

        permissions = payload.pop("permissions", None) or user.permissions.all()

        model_service = ModelService(self.request)

        user, error = model_service.update_model_instance(user, **payload)
        if error:
            return None, error

        # Attach roles to user
        user.roles.set(roles)
        user.permissions.set(permissions)

        return user, None

    def fetch_list(self, filter_params, **kwargs):
        keyword = filter_params.get("keyword")
        roles = filter_params.get("roles")

        q = Q()

        if keyword:
            q &= (Q(first_name__icontains=keyword) | Q(last_name__icontains=keyword) |
                  Q(email__icontains=keyword) | Q(phone_number__icontains=keyword) |
                  Q(user_id__icontains=keyword))

        if roles:
            roles = roles.split(",")
            q &= Q(role__id__in=roles)

        queryset = (User.available_objects.filter(q)
                    .exclude(user_id=self.auth_user.user_id)
                    .prefetch_related("roles").order_by("-created_at"))

        return queryset

    def fetch_creatable_users_roles(self):
        role_hierarchy_list = self.role_service.merge_user_roles_below_hierarchy()

        role_service = RoleService(self.request)
        roles = role_service.fetch_by_names(role_hierarchy_list)

        return roles, None
