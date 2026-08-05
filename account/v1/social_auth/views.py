from rest_framework.generics import CreateAPIView

from utils.service import CustomApiRequestProcessorBase
from .serializers import TokenSigninSerializer
from .services.facebook_service import FacebookService
from .services.google_service import GoogleService


class GoogleSigninAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    authentication_classes = []
    permission_classes = []
    serializer_class = TokenSigninSerializer

    def post(self, request, *args, **kwargs):
        service = GoogleService(request)
        return self.process_request(request, service.verify_token)


class FacebookSigninAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    authentication_classes = []
    permission_classes = []
    serializer_class = TokenSigninSerializer

    def post(self, request, *args, **kwargs):
        service = FacebookService(request)
        return self.process_request(request, service.verify_token)
