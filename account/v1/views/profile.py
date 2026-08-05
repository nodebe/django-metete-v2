from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from account.v1.serializers.profile import ProfileSerializer, PasswordResetSerializer, UserLocationSerializer
from account.v1.services.user import AccountService
from utils.constants import ResponseMessages
from utils.service import CustomApiRequestProcessorBase


class ProfileAPIView(RetrieveUpdateDestroyAPIView, CustomApiRequestProcessorBase):
    response_serializer = ProfileSerializer

    def put(self, request, *args, **kwargs):
        self.serializer_class = ProfileSerializer
        self.response_message_on_success = ResponseMessages.update_successful

        service = AccountService(request)

        return self.process_request(request, service.update)

    def get(self, request, *args, **kwargs):
        service = AccountService(request)

        return self.process_request(request, service.fetch)


class ProfileUserDataAPIView(RetrieveAPIView, CustomApiRequestProcessorBase):

    def get(self, request, *args, **kwargs):
        service = AccountService(request)

        return self.process_request(request, service.fetch_user_data)


class PasswordResetAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        service = AccountService(request)
        return self.process_request(request, service.reset_password)
