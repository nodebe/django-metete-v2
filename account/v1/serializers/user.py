from datetime import date
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from account.models import User
from account.v1.services.user import AccountService
from api.serializers.others import phone_number_serializer_validator
from media.models import UploadedMedia
from roles_permissions.models import Role
from utils.constants import ResponseMessages, ErrorMessages
from utils.errors import UserError, ValidationError

base_user_serializer_fields = ["first_name", "last_name", "phone_number", "profile_photo_id", "role_ids"]


class BaseUserSerializer(serializers.ModelSerializer):
    profile_photo_id = serializers.PrimaryKeyRelatedField(source="profile_photo", queryset=UploadedMedia.objects.all(),
                                                          required=False, allow_null=True)
    role_ids = serializers.PrimaryKeyRelatedField(source="roles", queryset=Role.objects.all(), many=True, required=True)


class UserSerializer(BaseUserSerializer):

    class Meta:
        model = User
        fields = base_user_serializer_fields + ["email"]


class CreateUserSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(source="role", queryset=Role.objects.all(), required=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "role_id"]

    def validate_phone_number(self, value):
        return phone_number_serializer_validator(value)

    def validate(self, attrs):
        data = attrs.copy()

        request = self.context.get("request")
        email = data.get('email')
        phone_number = data.get('phone_number')

        account_service = AccountService(request)

        is_email_exists, _ = account_service.check_email_exists(email)
        if is_email_exists:
            return ValidationError(ErrorMessages.email_already_exist, "email")

        is_phone_exists, _ = account_service.check_phone_number_exists(phone_number)
        if is_phone_exists:
            return ValidationError(ErrorMessages.phone_already_exist, "phone_number")

        year = date.today().year
        make_shift_password = f"{data["last_name"].capitalize()}-{year}"

        data["password"] = make_password(make_shift_password)

        return data


class UpdateUserSerializer(BaseUserSerializer):
    role_ids = serializers.PrimaryKeyRelatedField(source="roles", queryset=Role.objects.all(), many=True, required=False)
    phone_number = serializers.CharField(required=False)

    class Meta:

        model = User
        fields = base_user_serializer_fields
