import abc
import re
import cloudinary
import cloudinary.uploader
from abc import ABC
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class Uploader(ABC):
    video_extensions = ["mp4", "mov", "avi"]
    image_extensions = ["jpg", "jpeg", "png", "gif"]
    audio_extensions = ["mp3", "wav", "aac", "ogg", "flac", "m4a"]
    document_extensions = ["doc", "docx", "pdf", "ppt", "pptx"]

    def __init__(self, file_path=None, file_content=None, file_extension=None):
        self.file_path = file_path
        self.file_content = file_content
        self.file_extension = file_extension

    @abc.abstractmethod
    def upload(self):
        pass

    @abc.abstractmethod
    def delete(self):
        pass


class AmazonUploader(Uploader, ABC):
    def __init__(self, file_path=None, file_content=None, file_extension=None):
        super().__init__(file_path, file_content, file_extension)
        self.storage = S3Boto3Storage()

    def upload(self):
        file_name = f"{self.file_path}.{self.file_extension}"
        path = self.storage.save(file_name, self.file_content)

        url = settings.MEDIA_URL + path

        return url

    def delete(self):
        # Confirm this before usage.
        return self.storage.delete(self.file_path)


class CloudinaryUploader(Uploader, ABC):
    def __init__(self, file_path=None, file_content=None, file_extension=None):
        super().__init__(file_path, file_content, file_extension)

        # Configuration
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_API_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    def upload(self):
        resource_type = "image"

        if self.file_extension in self.video_extensions:
            resource_type = "video"
        elif self.file_extension in self.audio_extensions:
            resource_type = "raw"

        # Upload a file
        upload_result = cloudinary.uploader.upload(
            self.file_content,
            public_id=self.file_path,
            resource_type=resource_type,
            format=self.file_extension
        )

        url = upload_result.get("secure_url")

        return url

    def delete(self):
        match = re.search(r'upload/.*?/(.+?)(\.[^.]+)?$', self.file_path)
        if not match:
            raise ValueError(f"Could not extract public ID from URL: {self.file_path}")

        public_id = match.group(1)

        # Delete the file
        result = cloudinary.uploader.destroy(public_id)

        return True
