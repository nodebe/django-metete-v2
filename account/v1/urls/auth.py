from django.urls import path
from account.v1.views.auth import (LoginAPIView, ForgotPasswordAPIView, VerifyPasswordOTPAPIView,
                                   PasswordResetOTPAPIView, CustomTokenRefreshAPIView, VerifyTwoFactorAuthOTPAPIView,
                                   ResendTwoFactorOTPAPIView)

urlpatterns = [
    path("login", LoginAPIView.as_view(), name='login'),
    path("password/forgot", ForgotPasswordAPIView.as_view(), name='forgot_password'),
    path("password/reset", PasswordResetOTPAPIView.as_view(), name='reset_password'),
    path("password/verify-otp", VerifyPasswordOTPAPIView.as_view(), name='verify_password_otp'),
    path('token/refresh', CustomTokenRefreshAPIView.as_view(), name='token_refresh'),
    path("verify-otp/2fa", VerifyTwoFactorAuthOTPAPIView.as_view(), name='verify_two_factor_otp'),
    path("resend-otp/2fa", ResendTwoFactorOTPAPIView.as_view(), name='resend_two_factor_otp'),
]
