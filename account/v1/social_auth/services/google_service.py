from account.v1.social_auth.constants import AuthProviders
from account.v1.social_auth.services.util import SocialAuthService
from utils.constants import ErrorMessages
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings


class GoogleService(SocialAuthService):
    """
    Make sure to set in your settings:
    GOOGLE_OAUTH_KEYS: {
        WEB_CLIENT_KEY_1,
        WEB_CLIENT_KEY_2,
        WEB_CLIENT_KEY_3,
    }
    """
    def __init__(self, request):
        super().__init__(request)
        self.auth_provider = AuthProviders.google

    def verify_token(self, payload):
        token = payload.get("token")

        request = requests.Request()
        id_info = {}

        try:
            # Make request to google server
            id_info = id_token.verify_oauth2_token(token, request)
        except Exception as e:
            if "Token expired" in str(e):
                return None, self.make_401(ErrorMessages.token_expired)

        auth_keys = settings.GOOGLE_OAUTH_KEYS or []

        if id_info.get('aud') not in auth_keys:
            return None, self.make_400(ErrorMessages.user_not_recognized)

        id_info["user_id"] = id_info.get("sub")
        id_info["first_name"] = id_info.get("given_name")
        id_info["last_name"] = id_info.get("family_name")

        user = self.get_or_create_user(payload=id_info)

        return self.get_user_data(user), None
