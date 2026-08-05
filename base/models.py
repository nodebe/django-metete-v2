from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class MailSenderOptions(models.TextChoices):
    smtp = "SMTP"
    mailjet = "MAILJET"


MailSenderOptionsFromEmail = {
    MailSenderOptions.smtp: settings.DEFAULT_FROM_EMAIL_SMTP,
    MailSenderOptions.mailjet: settings.DEFAULT_FROM_EMAIL_MJ
}


class QuerySetManagerTypes(models.TextChoices):
    objects = "objects"
    deleted_objects = "deleted_objects"
    active_available_objects = "active_available_objects"
    available_objects = "available_objects"
    active_objects = "active_objects"


class AvailableManager(models.Manager):
    """Fetches all available records"""

    def get_queryset(self):
        return super(AvailableManager, self).get_queryset().filter(is_deleted=False)


class DeletedManager(models.Manager):
    """Fetches all deleted records"""

    def get_queryset(self):
        return super(DeletedManager, self).get_queryset().filter(is_deleted=True)


class ActiveManager(models.Manager):
    """Fetches all active records"""

    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(is_active=True)


class ObjectManager(models.Manager):
    """Fetches all records related to an object."""

    def get_queryset(self):
        return super(ObjectManager, self).get_queryset()


class ActiveAvailableManager(models.Manager):
    """Fetches records that are currently available and active as well"""

    def get_queryset(self):
        return super(ActiveAvailableManager, self).get_queryset().filter(
            is_active=True, is_deleted=False
        )


class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("account.User", on_delete=models.SET_NULL, null=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey("account.User", null=True, on_delete=models.SET_NULL, related_name="+")
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey("account.User", null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name="+")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey("account.User", null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="+")
    history = HistoricalRecords(inherit=True)

    def model_name(self):
        return self._meta.model_name

    active_available_objects = ActiveAvailableManager()
    active_objects = ActiveManager()
    available_objects = AvailableManager()
    deleted_objects = DeletedManager()
    objects = ObjectManager()

    class Meta:
        abstract = True


class AppDbModel(models.Model):
    objects = ObjectManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def model_name(self):
        return self._meta.model_name

    class Meta:
        abstract = True


class Activity(AppDbModel):
    user = models.ForeignKey("account.User", on_delete=models.SET_NULL, null=True, related_name="activity")
    activity_type = models.CharField(max_length=255, null=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "{} by {} - {}".format(self.activity_type, self.user, self.note)

    class Meta:
        verbose_name_plural = "Activities"


class ApiRequestLogger(AppDbModel):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, null=True, related_name="+")
    path = models.CharField(max_length=255)
    ref_id = models.CharField(null=False, db_index=True, max_length=255)
    headers = models.JSONField(default=dict)
    request_data = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "API Request Logs"


class MailSender(AppDbModel):
    name = models.CharField(max_length=255, choices=MailSenderOptions.choices, default=MailSenderOptions.smtp)
