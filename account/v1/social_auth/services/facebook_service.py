from account.v1.social_auth.constants import AuthProviders
from account.v1.social_auth.services.util import SocialAuthService
from utils.constants import ErrorMessages
import requests
from django.conf import settings


class FacebookService(SocialAuthService):
    """
    Make sure to set in your settings:
    SOCIAL_AUTH_FACEBOOK_KEY: Your Facebook App ID
    SOCIAL_AUTH_FACEBOOK_SECRET: Your Facebook App Secret
    set the scope in the client side to "public_profile,email"
    """

    def __init__(self, request):
        super().__init__(request)
        self.auth_provider = AuthProviders.facebook
        self.GRAPH_API_URL = "https://graph.facebook.com/v18.0"

    def verify_token(self, payload):
        token = payload.get("token")

        if not token:
            return None, self.make_401(ErrorMessages.invalid_token_retry_login)

        # Step 1: Verify the token with Facebook
        app_id = settings.SOCIAL_AUTH_FACEBOOK_KEY
        app_secret = settings.SOCIAL_AUTH_FACEBOOK_SECRET

        # Debug token endpoint
        debug_token_url = f"{self.GRAPH_API_URL}/debug_token"
        params = {
            "input_token": token,
            "access_token": f"{app_id}|{app_secret}"  # App access token
        }

        debug_response = requests.get(debug_token_url, params=params)
        debug_data = debug_response.json()

        # Check if token is valid
        if not debug_data.get("data", {}).get("is_valid", False):
            error_message = debug_data.get("data", {}).get("error", {}).get("message",
                                                                            ErrorMessages.invalid_token_retry_login)
            if "expired" in error_message.lower():
                return None, self.make_401(ErrorMessages.token_expired)
            return None, self.make_401(error_message)

        # Step 2: Get user data from Facebook
        user_data_url = f"{self.GRAPH_API_URL}/me"
        fields = "id,email,first_name,last_name,name,picture.type(large)"
        params = {
            "fields": fields,
            "access_token": token
        }

        user_response = requests.get(user_data_url, params=params)
        user_data = user_response.json()

        # Check if the app ID matches
        if str(debug_data.get("data", {}).get("app_id")) != str(app_id):
            return None, self.make_400(ErrorMessages.user_not_recognized)

        user_id = str(user_data.get("id"))
        user_data["user_id"] = user_id

        email = user_data.get("email")

        if not email:
            user_data["email"] = f"{user_id}@facebook.com"

        user = self.get_or_create_user(payload=user_data)

        return self.get_user_data(user), None
