from django.contrib.auth.hashers import make_password
from password_validator import PasswordValidator
from rest_framework import serializers
from account.v1.services.user import AccountService
from utils.constants import ErrorMessages
from utils.errors import ValidationError
from utils.service import invalid_input_checker


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        data = attrs.copy()

        password = attrs.get("password", "")
        email = data.get("email")
        request = self.context.get("request")

        password_schema = PasswordValidator()
        password_schema.min(12).uppercase().lowercase().digits().symbols()

        if not password_schema.validate(password):
            return ValidationError(ErrorMessages.insecure_password, code="password")

        data["password"] = make_password(password)

        if email:
            account_service = AccountService(request)
            user_exists, _ = account_service.check_email_exists(email)

            if user_exists:
                return ValidationError(ErrorMessages.email_already_exist, code="email")
            
            _, error_key = invalid_input_checker({"email": email})

            if error_key:
                return ValidationError(ErrorMessages.invalid_input, code=error_key)

        return data


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

        data["password"] = password

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
