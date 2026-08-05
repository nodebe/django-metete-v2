from django.conf import settings
from django.core.files.base import ContentFile
import time
from media.models import UploadToChoices, UploadedMedia
from utils.constants import ErrorMessages
from utils.service import CustomApiRequestProcessorBase
from utils.uploaders import AmazonUploader, CloudinaryUploader


class DataBucketPicker:
    def __init__(self):
        pass

    def pick_uploader(self):
        if settings.DATA_BUCKET == "AWS":
            return AmazonUploader
        elif settings.DATA_BUCKET == "CLOUDINARY":
            return CloudinaryUploader
        raise ValueError("No Data Bucket defined.")


class FileUploader(CustomApiRequestProcessorBase):
    DEFAULT_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]

    def __init__(self, request):
        super().__init__(request)
        self.request = request
        self.upload_to = UploadToChoices.general

    def upload(self, file, description_payload):
        original_file_name = file.name.lower()
        file_extension = original_file_name.split('.')[-1].lower()
        file_size = self.get_file_size(file)

        media_type = description_payload.get("media_type")

        if not media_type:
            return None, self.make_404(ErrorMessages.media_type_not_found)

        allowed_file_types = [aft.strip(".") for aft in media_type.allowed_file_types]

        if file_extension not in allowed_file_types:
            return None, self.make_400(ErrorMessages.invalid_file_extension)

        if file_size > (media_type.max_file_size_in_kb * 1024):
            return None, self.make_400(ErrorMessages.file_too_large)

        self.upload_to = media_type.upload_to

        file_path = f"{self.upload_to}/{self.generate_file_name(file_extension)}"
        file_content = ContentFile(file.read())

        data_bucket = DataBucketPicker().pick_uploader()
        uploader = data_bucket(file_path, file_content, file_extension)

        full_url = uploader.upload()

        uploaded_file = UploadedMedia.objects.create(
            media=media_type,
            user=self.auth_user,
            url=full_url,
            name=original_file_name.strip(f".{file_extension}"),
            size=file_size,
            file_type=self.get_content_type_from_extension(file_extension)
        )

        return uploaded_file, None

    def generate_file_name(self, ext):
        file_name = f"{str(time.time()).replace('.', '')}{str(time.time()).replace('.', '')}"
        return file_name

    def delete(self, file_path):
        data_bucket = DataBucketPicker().pick_uploader()
        uploader = data_bucket(file_path)
        return uploader.delete(), None

    def get_file_size(self, file):
        original_position = file.tell()  # Store the original position
        file.seek(0, 2)  # Move the file pointer to the end of the file
        file_size = file.tell()  # Get the current position (file size)
        file.seek(original_position)  # Return to the original position
        return file_size

    def get_content_type_from_extension(self, file_extension):
        extension_mapping = {
            'txt': 'text/plain',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'mp4': 'video/mp4',
            'mp3': 'audio/mp3',
            'html': 'text/html',
            'css': 'text/css',
        }

        return extension_mapping.get(file_extension, 'application/octet-stream')
