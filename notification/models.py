from django.db import models
from django.db.models import TextChoices
from base.models import BaseModel


class MessageTypes(TextChoices):
    password_reset = "Password Reset"
    dynamic_notification = "Dynamic Notification"
    send_2fa_otp = "Two-Factor Authentication"


class NotificationType(TextChoices):
    email = "Email"
    sms = "SMS"
    whatsapp = "WhatsApp"


class MessageTemplate(BaseModel):
    type = models.CharField(choices=MessageTypes.choices, max_length=500, unique=True)
    email_template = models.TextField(null=True, blank=True)
    email_subject = models.CharField(null=True, blank=True, max_length=1000)
    in_app_message = models.CharField(null=True, blank=True, max_length=1000)
    sms_message = models.CharField(null=True, blank=True, max_length=1000)
    whatsapp_message = models.TextField(null=True, blank=True)
    description = models.CharField(null=True, max_length=1000)

    class Meta:
        ordering = ['type']

    def __str__(self):
        return "{}".format(self.type)


class MessageVariable(BaseModel):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=1000, null=True)
    template = models.ForeignKey(MessageTemplate, on_delete=models.CASCADE, related_name="template_variables")

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'template'),)

    def __str__(self):
        return "{} - {}".format(self.name, self.template)
