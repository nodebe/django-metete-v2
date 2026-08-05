from django.db import models
from base.models import AppDbModel


class UploadToChoices(models.TextChoices):
    images = "images"
    videos = "videos"
    audio = "audios"
    document = "documents"
    general = "general"


class Media(AppDbModel):
    """
    This is a list of the kind of media that can be stored on the system. e.g. profile picture, document file, etc.
    """
    name = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    allowed_file_types = models.JSONField(blank=True)
    max_file_size_in_kb = models.PositiveIntegerField(default=1000)
    upload_to = models.CharField(max_length=50, blank=False, null=False, choices=UploadToChoices.choices,
                                 default=UploadToChoices.general)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Media"

    def __str__(self):
        return "{}".format(self.name)


class UploadedMedia(AppDbModel):
    user = models.ForeignKey("account.User", null=True, on_delete=models.CASCADE)
    url = models.URLField()
    name = models.CharField(max_length=255)
    size = models.IntegerField(null=True)
    file_type = models.CharField(max_length=255, null=True)
    media = models.ForeignKey("media.Media", null=True, on_delete=models.SET_NULL, related_name="uploads")

    class Meta:
        verbose_name_plural = "Uploaded Media"

    def __str__(self):
        return f"{self.name}::{self.file_type}"
