from rest_framework.generics import CreateAPIView
from utils.constants import ResponseMessages
from ..serializers.auth import (LoginSerializer, ResetPasswordSerializer, VerifyUserOTPSerializer, EmailSerializer,
                                RefreshTokenSerializer)
from ..services.auth import AuthService, OTPIntent
from utils.service import CustomApiRequestProcessorBase


class LoginAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = LoginSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        self.response_message_on_success = ResponseMessages.login_successful
        return self.process_request(request, service.login)


class ForgotPasswordAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = EmailSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.send_otp, otp_intent=OTPIntent.reset_password)


class VerifyPasswordOTPAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = VerifyUserOTPSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.verify_password_otp)


class VerifyTwoFactorAuthOTPAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = VerifyUserOTPSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.verify_2fa_otp)


class ResendTwoFactorOTPAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = EmailSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.send_otp, otp_intent=OTPIntent.two_fa_verification)


class PasswordResetOTPAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = ResetPasswordSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.reset_password)


class CustomTokenRefreshAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = RefreshTokenSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.refresh_token)

