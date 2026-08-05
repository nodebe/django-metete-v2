from abc import ABC, abstractmethod

from account.v1.models.user import User, AuthProviders
from utils.service import CustomApiRequestProcessorBase


class SocialAuthService(CustomApiRequestProcessorBase, ABC):
    def __init__(self, request):
        super().__init__(request)
        self.auth_provider = None

    def get_or_create_user(self, payload):
        user_id = payload.get("user_id")
        email = payload.get("email")

        username = email.split("@")[0] + user_id[10:]

        user, is_created = User.objects.get_or_create(
            email=email,
            defaults={
                "user_id": user_id,
                "phone_number": user_id,
                "username": username,
                "first_name": payload.get("first_name"),
                "last_name": payload.get("last_name"),
                "auth_provider": self.auth_provider
            }
        )

        # if is_created:
        #     picture = payload.get("picture")
        #     user.profile_picture = self.insert_profile_picture(user, picture)
        #     user.save(update_fields=["profile_picture"])

        return user

    # def insert_profile_picture(self, user, picture_link):
    #     return UploadedMedia.objects.create(
    #         url=picture_link,
    #         name=user.get_full_name(),
    #     )

    @abstractmethod
    def verify_token(self, payload):
        pass

    def get_user_data(self, user):
        return {
            **user.tokens,
            "token_type": "Bearer",
            "user": {
                "id": user.user_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "account_type": user.account_type,
            }
        }