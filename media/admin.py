from django.contrib import admin
from .models import Media, UploadedMedia


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ["name", "label", "allowed_file_types", "max_file_size_in_kb"]


@admin.register(UploadedMedia)
class UploadedMediaAdmin(admin.ModelAdmin):
    list_display = ["id", "url", "name", "size", "file_type"]
