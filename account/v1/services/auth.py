from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.db.models import TextChoices
from rest_framework_simplejwt.tokens import RefreshToken
from notification.tasks import send_password_reset, send_2fa_otp
from utils.constants import ResponseMessages, ErrorMessages
from utils.models import ModelService
from .user import AccountService
from utils.service import CustomApiRequestProcessorBase, generate_otp, check_time_expired
from django.utils import timezone
from ...models.user import Otp


class OTPIntent(TextChoices):
    reset_password = "Reset Password"
    two_fa_verification = "Two Factor Verification"


class AuthService(CustomApiRequestProcessorBase):
    def __init__(self, request):
        super(AuthService, self).__init__(request)
        self.model_service = ModelService(request)
        self.account_service = AccountService(request)

    def reset_password(self, payload):
        email = payload.get("email")
        password = payload.get("password")

        account_service = AccountService(self.request)

        user_exists, user = account_service.check_email_exists(email)

        if not user_exists:
            return None, self.make_400(ErrorMessages.user_not_recognized)

        if not user.can_reset_password:
            return None, self.make_403(ErrorMessages.access_denied)

        user.password = password
        user.can_reset_password = False
        user.save(update_fields=["password", "can_reset_password"])

        self.report_activity(user=user, description="Password reset successful")

        return ResponseMessages.successful_password_change, None

    def send_otp(self, payload, otp_intent=None, user=None):
        if user is None:
            email = payload.get("email")
            account_service = AccountService(self.request)
            user_exists, user = account_service.check_email_exists(email)
        else:
            user_exists, user = True, user
            email = user.email

        if user_exists:
            otp_service = OTPService(self.request)
            otp = otp_service.get_or_set_user_otp(user)

            if otp_intent == OTPIntent.reset_password:
                _ = send_password_reset.delay(phone_number_or_email=email, otp=otp)
            elif otp_intent == OTPIntent.two_fa_verification:
                _ = send_2fa_otp.delay(phone_number_or_email=email, otp=otp, first_name=user.first_name)
                return {
                    "redirect_to_2fa": True
                }, None

        return ResponseMessages.otp_sent_to_email, None

    def verify_otp_via_email(self, payload, otp_intent=None):
        """
        :param otp_intent: used to determine what happens after verifying otp
        :param payload: {
            otp: 6-digit code,
            email: "nody@example.com"
        }
        :return: User or Message
        """
        otp = payload.get("otp")
        email = payload.get("email")

        account_service = AccountService(self.request)
        user_exists, user = account_service.check_email_exists(email)

        if not (user_exists and hasattr(user, "otp")):
            return None, self.make_400(ErrorMessages.user_not_recognized)

        otp_service = OTPService(self.request)

        is_verified, error = otp_service.verify_otp(user, otp)
        if error:
            return None, error

        if not is_verified:
            return None, self.make_400(ErrorMessages.invalid_or_expired_otp)

        if otp_intent == OTPIntent.reset_password:
            user.can_reset_password = True
            user.save(update_fields=["can_reset_password"])
            return ResponseMessages.valid_otp, None

        elif otp_intent == OTPIntent.two_fa_verification:
            self.report_activity(user=user, description="Log in to account")
            return account_service.get_user_data(user), None

        return None, self.make_400(ErrorMessages.invalid_or_expired_otp)

    def verify_password_otp(self, payload):
        return self.verify_otp_via_email(payload, otp_intent=OTPIntent.reset_password)

    def verify_2fa_otp(self, payload):
        return self.verify_otp_via_email(payload, otp_intent=OTPIntent.two_fa_verification)

    def increment_login_count(self, login_count_cache_key):
        login_count = cache.get(key=login_count_cache_key)

        login_count = 1 if login_count is None else login_count + 1
        cache.set(login_count_cache_key, login_count, timeout=1200)

        if login_count and login_count >= settings.MAX_LOGIN_ATTEMPTS:
            return self.make_403(ErrorMessages.too_many_attempts_account_blocked)

        return None

    def login(self, payload):
        email = payload.get("email").lower()
        password = payload.get("password")

        account_service = AccountService(self.request)
        user_exists, user = account_service.check_email_exists(email)

        if user and not user.is_active:
            return None, self.make_403(ErrorMessages.inactive_account)

        login_count_cache_key = self.generate_cache_key("login_count", email)

        if user is None:
            error = self.increment_login_count(login_count_cache_key)
            return None, error or self.make_400(ErrorMessages.invalid_credentials)

        if not check_password(password, user.password):
            error = self.increment_login_count(login_count_cache_key)
            return None, error or self.make_400(ErrorMessages.invalid_credentials)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        if not user.is_2fa_set:
            account_service = AccountService(request=self.request)

            return account_service.get_user_data(user), None

        return self.send_otp(payload={}, otp_intent=OTPIntent.two_fa_verification, user=user)

    def refresh_token(self, payload):
        token = payload.get('refresh_token')

        if not token:
            return None, self.make_403(ErrorMessages.access_denied)

        try:
            refresh = RefreshToken(token)

        except Exception:
            return None, self.make_401(ErrorMessages.token_expired)

        return {"access_token": str(refresh.access_token)}, None


class OTPService(CustomApiRequestProcessorBase):
    def __init__(self, request):
        super().__init__(request)

    def create(self, data):
        model_service = ModelService(self.request)

        _ = model_service.create_model_instance(model=Otp, payload=data)

        return True

    def get_or_set_user_otp(self, user):
        """Creates the OTP one-to-one relationship for the user if not existing or creates a new OTP and attaches it
        to the already existing relationship"""
        otp, hashed_otp = generate_otp()

        data = {
            "user": user,
            "otp": hashed_otp,
            "otp_requested_at": timezone.now()
        }

        if not hasattr(user, "otp"):
            _ = self.create(data)

        else:
            _ = self.update_user_otp(user, hashed_otp)

        return otp

    def update_user_otp(self, user, hashed_otp):
        user_otp = user.otp
        user_otp.otp = hashed_otp
        user_otp.trials = 0
        user_otp.otp_requested_at = timezone.now()
        user_otp.otp_verified_at = None
        user_otp.is_otp_verified = False
        user_otp.save(update_fields=["otp", "otp_requested_at", "trials", "is_otp_verified", "otp_verified_at"])

        return True

    def verify_otp(self, user, incoming_otp):
        user_otp = user.otp

        if user_otp.trials >= 3:
            return None, self.make_400(ErrorMessages.too_many_failed_otp_verification_attempts)

        if user_otp.is_otp_verified:
            return None, self.make_400(ErrorMessages.invalid_or_expired_otp)

        otp_requested_at = user_otp.otp_requested_at
        hashed_otp = user_otp.otp

        is_expired = check_time_expired(otp_requested_at)

        if check_password(incoming_otp, hashed_otp) and not is_expired:
            user_otp.is_otp_verified = True
            user_otp.otp_verified_at = timezone.now()
            user_otp.save(update_fields=["is_otp_verified", "otp_verified_at"])

            return True, None

        user_otp.trials += 1
        user_otp.save(update_fields=["trials"])

        return False, None
