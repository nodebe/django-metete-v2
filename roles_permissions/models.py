from django.db import models
from django.utils.text import slugify
from base.models import BaseModel


class Permission(models.Model):
    objects = None
    name = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=255)
    group_name = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # If label is not manually set, generate it from name
        if not self.label:
            self.label = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Role(BaseModel):
    name = models.CharField(max_length=255, null=True)
    label = models.CharField(max_length=255, null=False, unique=True)
    description = models.TextField(null=True, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, db_table="role_permissions")
    user_can_be_created_by = models.JSONField(null=True, blank=True)
    is_default = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # If label is not manually set, generate it from name
        if not self.label:
            self.label = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
