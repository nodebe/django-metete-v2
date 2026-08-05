from rest_framework import serializers
from .models import UploadedMedia, Media
from .services import MediaService


class UploadMediaSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    media_type_id = serializers.CharField(required=True)

    def validate(self, attrs):
        data = attrs.copy()

        request = self.context.get("request")
        media_type_id = data.get("media_type_id")

        service = MediaService(request)

        media_type, error = service.find_media_type_by_id(media_type_id)

        if error:
            raise serializers.ValidationError(error.get_message())

        data["media_type"] = media_type

        return data


class UploadMediaResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedMedia
        fields = ["id", "url", "name", "size", "file_type"]


class MediaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "name", "label", "description", "allowed_file_types", "max_file_size_in_kb"]
