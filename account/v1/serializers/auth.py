from django.contrib.auth.hashers import make_password
from password_validator import PasswordValidator
from rest_framework import serializers
from utils.constants import ErrorMessages
from utils.errors import ValidationError


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        data = attrs.copy()

        password = attrs.get("password", "")

        password_schema = PasswordValidator()
        password_schema.min(12).uppercase().lowercase().digits().symbols()

        if not password_schema.validate(password):
            return ValidationError(ErrorMessages.insecure_password, code="password")

        data["password"] = make_password(password)

        return data


class VerifyUserOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
