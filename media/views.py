from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from .serializers import MediaTypeSerializer, UploadMediaSerializer, UploadMediaResponseSerializer
from .services import MediaService
from utils.service import CustomApiRequestProcessorBase


class MediaTypeAPIView(ListAPIView, CustomApiRequestProcessorBase):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        self.response_serializer = MediaTypeSerializer
        self.response_serializer_requires_many = True

        service = MediaService(request)
        return self.process_request(request, target_function=service.fetch_media_types)


class UploadMediaAPIView(CreateAPIView, CustomApiRequestProcessorBase):
    permission_classes = [IsAuthenticated]
    serializer_class = UploadMediaSerializer

    def post(self, request, *args, **kwargs):
        self.logging_enabled = False
        self.request_payload_requires_decryption = False
        self.response_payload_requires_encryption = False
        self.response_serializer = UploadMediaResponseSerializer
        self.response_serializer_requires_many = True
        service = MediaService(request)

        return self.process_request(request, target_function=service.upload_media)


class DeleteMediaAPIView(DestroyAPIView, CustomApiRequestProcessorBase):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        service = MediaService(request)

        media_id = kwargs.get('media_id')

        return self.process_request(request, target_function=service.delete_media, media_id=media_id)
