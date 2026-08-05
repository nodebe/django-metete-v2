from .models import Media, UploadedMedia
from utils.errors import OperationError, ServerError
from utils.service import CustomApiRequestProcessorBase
from utils.uploader_util import FileUploader
from utils.constants import ResponseMessages, ErrorMessages


class MediaService(CustomApiRequestProcessorBase):
    def __init__(self, request):
        super().__init__(request)

    def upload_media(self, payload):
        files = self.request.FILES.getlist("file")

        if not files:
            return None, self.make_400(ErrorMessages.invalid_file)

        file_uploader = FileUploader(request=self.request)

        uploaded_file_list = []

        for file in files:
            uploaded_file, error = file_uploader.upload(file=file, description_payload=payload)
            if error:
                return None, error

            uploaded_file_list.append(uploaded_file)

        return uploaded_file_list, None

    def delete_media(self, media_id):
        uploaded_media = UploadedMedia.objects.filter(id=media_id).first()

        if not uploaded_media:
            return None, self.make_404(ErrorMessages.media_not_found)

        is_owner, error = self.check_resource_owner(uploaded_media, ErrorMessages.permission_denied)
        if error:
            return None, error

        # Delete from Cloud storage
        file_uploader = FileUploader(request=self.request)
        _, error = file_uploader.delete(file_path=uploaded_media.url)
        if error:
            return None, error

        uploaded_media.delete()

        return ResponseMessages.media_deleted_successfully, None

    def find_media_type_by_id(self, media_type_id):
        if not str(media_type_id).isdigit():
            return None, self.make_404(ErrorMessages.media_type_not_found)

        def __do_fetch_single():
            try:
                return Media.objects.get(pk=media_type_id), None

            except Media.DoesNotExist:
                return None, self.make_404(ErrorMessages.media_type_not_found)

            except Exception as e:
                server_error = ServerError(error=e, obj=self)
                return None, OperationError(
                    self.request, message=server_error.message, status_code=server_error.status_code
                )

        cache_key = self.generate_cache_key("media_type", media_type_id)
        return self.get_cache_value_or_default(cache_key, __do_fetch_single)

    def find_uploaded_media_by_id(self, media_id, many=False):
        if not many and not str(media_id).isdigit():
            return None, self.make_404(ErrorMessages.media_not_found)

        def __do_fetch_single():
            try:
                if many:
                    return UploadedMedia.objects.filter(pk__in=media_id).all(), None

                return UploadedMedia.objects.get(pk=media_id), None

            except UploadedMedia.DoesNotExist:
                return None, self.make_404(ErrorMessages.media_not_found)

            except Exception as e:
                server_error = ServerError(error=e, obj=self)
                return None, OperationError(
                    self.request, message=server_error.message, status_code=server_error.status_code
                )

        cache_key = self.generate_cache_key("uploaded_media", media_id)
        return self.get_cache_value_or_default(cache_key, __do_fetch_single)

    def fetch_media_types(self):
        def __do_fetch():
            try:
                return Media.objects.all().order_by("id"), None

            except Exception as e:
                server_error = ServerError(error=e, obj=self)
                return None, OperationError(
                    self.request, message=server_error.message, status_code=server_error.status_code
                )

        cache_key = self.generate_cache_key("media_types")
        return self.get_cache_value_or_default(cache_key, __do_fetch)
    