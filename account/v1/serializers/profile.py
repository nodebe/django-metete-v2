from django.contrib.auth.hashers import make_password
from password_validator import PasswordValidator
from rest_framework import serializers
from account.models.user import User
from location.v1.serializers import LocationSerializer
from roles_permissions.serializers import SimpleRoleSerializer
from media.models import UploadedMedia
from utils.constants import ResponseMessages, ErrorMessages
from utils.errors import UserError, ValidationError
from utils.service import format_phone_number
import datetime


class VerySimpleProfileSerializer(serializers.ModelSerializer):
    profile_photo = serializers.URLField(source="profile_photo.url", read_only=True, default=None)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["user_id", "first_name", "last_name", "username", "email", "phone_number", "profile_photo", "role"]

    def get_role(self, obj):
        first_role = obj.roles.first()
        if first_role:
            return obj.roles.first().name
        return None


base_profile_serializer_fields = ['user_id', 'first_name', 'last_name', 'username', 'phone_number', 'email',
                                  "profile_photo", "roles", "created_at", "is_active", "username", "address"]


class BaseProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    profile_photo = serializers.URLField(source="profile_photo.url", read_only=True, default=None)
    created_by = VerySimpleProfileSerializer(read_only=True)


class ProfileSerializer(BaseProfileSerializer):
    profile_photo_id = serializers.PrimaryKeyRelatedField(source="profile_photo", queryset=UploadedMedia.objects.all(),
                                                          required=False, write_only=True)
    updated_by = VerySimpleProfileSerializer(read_only=True)
    deactivated_by = VerySimpleProfileSerializer(read_only=True)
    roles = SimpleRoleSerializer(read_only=True, many=True)
    address = LocationSerializer(required=False)
    is_verified = serializers.BooleanField(read_only=True)
    phone_number = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = base_profile_serializer_fields + ["is_active", "profile_photo_id", "updated_by", "updated_at",
                                                   "deactivated_by", "deactivated_at", "is_verified"]

        extra_kwargs = {
            "phone_number": {"validators": []}
        }

    def validate_phone_number(self, value):
        formatted_phone_number, error = format_phone_number(value)

        if error:
            return error

        if not formatted_phone_number:
            return ValidationError(ErrorMessages.invalid_phone_number, code="phone_number")

        return formatted_phone_number


class SimpleProfileSerializer(BaseProfileSerializer):
    role = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = User
        fields = base_profile_serializer_fields


class PasswordResetSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        data = attrs.copy()

        password = attrs.get("new_password", "")

        password_schema = PasswordValidator()
        password_schema.min(8).uppercase().lowercase().digits().symbols()

        if not password_schema.validate(password):
            return ValidationError(ErrorMessages.insecure_password, "password")

        data["new_password"] = make_password(password)

        return data


class SiteUserSerializer(serializers.ModelSerializer):
    roles = SimpleRoleSerializer(read_only=True, many=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = base_profile_serializer_fields + ["tokens", "id"]

    def get_tokens(self, obj):
        tokens = obj.tokens
        if tokens:
            access_token = tokens.get("access_token")
            expiry_time = tokens.get("expiry")
            expires_at = datetime.datetime.now() + expiry_time

            return {
                "access_token": access_token,
                "expiry": expires_at
            }
        return None


class UserLocationSerializer(serializers.Serializer):
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
