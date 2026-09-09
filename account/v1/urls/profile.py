from django.urls import path

from account.v1.views.profile import ProfileAPIView, ProfileUserDataAPIView, PasswordResetAPIView, Setup2FAAPIView


urlpatterns = [
    path("", ProfileAPIView.as_view(), name="profile"),
    path("user-data", ProfileUserDataAPIView.as_view(), name="profile_user_data"),
    path("settings/password", PasswordResetAPIView.as_view(), name='password_reset'),
    path("settings/2fa", Setup2FAAPIView.as_view(), name="setup_2fa"),
]
