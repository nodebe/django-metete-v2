from django.urls import path

from .views import MediaTypeAPIView, UploadMediaAPIView, DeleteMediaAPIView

app_name = "media"

urlpatterns = [
    path("types", MediaTypeAPIView.as_view(), name='media_type'),
    path("upload", UploadMediaAPIView.as_view(), name='upload_media'),
    path("delete", DeleteMediaAPIView.as_view(), name='delete_media'),
]
