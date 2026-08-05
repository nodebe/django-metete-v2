import os
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template import Context, Template
from mailjet_rest import Client
from base.models import MailSender, MailSenderOptions, MailSenderOptionsFromEmail
from .models import MessageTypes, MessageTemplate, MessageVariable, NotificationType
from utils.service import AppLogger

APP_NAME = settings.APP_INFO_DEFAULTS.get("app_name")

notifications = {
    MessageTypes.password_reset: {
        "file": "reset-password.html",
        "description": "Password Reset OTP",
        "in_app_message": "",
        "email_subject": "Password Reset",
        "sms_message": "",
        "variables": [
            {"name": "first_name", "description": "First Name"},
            {"name": "otp", "description": "One-Time Password"}
        ]
    },
    MessageTypes.dynamic_notification: {
        "file": "dynamic-notification.html",
        "description": "Dynamic Notification",
        "in_app_message": "",
        "email_subject": "Notification",
        "sms_message": "",
        "variables": [
            {"name": "username", "description": "Username"},
            {"name": "message", "description": "Message to the user"}
        ]
    },

    MessageTypes.send_2fa_otp: {
        "file": "send-2fa-otp.html",
        "description": "Two Factor Authentication OTP",
        "in_app_message": "",
        "sms_message": "",
        "email_subject": "Two-Factor Authentication OTP",
        "variables": [
            {"name": "first_name", "description": "First Name"},
            {"name": "otp", "description": "One-Time Password"}
        ]
    },
}


class NotificationUtil:

    def __init__(self, notification_type=NotificationType.email):
        self.notification_type = notification_type
        self.defaults = settings.APP_INFO_DEFAULTS

    def send_notification(self, recipients, message_type: str, data: dict):
        template = get_notification_template_for(message_type)

        if not template:
            return "No template found for this type."

        data.update(self.defaults.copy())

        if self.notification_type == NotificationType.email:
            return self.send_email_from_template(template=template, emails=recipients, data=data)
        elif self.notification_type == NotificationType.sms:
            return self.send_sms_from_template(template=template, recipients=recipients, data=data)
        elif self.notification_type == NotificationType.whatsapp:
            pass

        return None

    def send_email_from_template(self, template, emails, data: dict):
        message = render_to_template(template.email_template, data)
        subject = render_to_template(template.email_subject, data)

        return self.send_email(emails, subject, message)

    def send_sms_from_template(self, template, recipients, data: dict):
        message = render_to_template(template.sms_message or "", data)
        return self.send_sms(recipients, message)

    def send_sms(self, recipients, message):
        # TODO: Update to use sms service
        pass

    def mail_sender(self):
        def __do_fetch():
            return MailSender.objects.first().name

        cache_key = "mail_sender"
        return cache.get_or_set(cache_key, __do_fetch, 300)

    def send_email(self, emails, subject, mail_body, from_email=None):
        if not emails:
            emails = settings.SYSTEM_DEFAULT_EMAIL_RECIPIENTS

        if settings.DEBUG:
            subject = "[Test] " + subject

        if isinstance(emails, str):
            receivers = [emails]
        else:
            receivers = [email for email in emails if email]
        valid_emails = []

        for email in receivers:
            try:
                validate_email(email)
            except ValidationError as e:
                pass
            else:
                valid_emails.append(email)
        if not valid_emails:
            return

        MAIL_SENDER = self.mail_sender().upper()

        if not from_email:
            from_email = MailSenderOptionsFromEmail.get(MAIL_SENDER)

        if MAIL_SENDER == MailSenderOptions.smtp:
            self.send_via_smtp(receivers=valid_emails, subject=subject, mail_body=mail_body, from_email=from_email)
        elif MAIL_SENDER == MailSenderOptions.mailjet:
            self.send_via_mailjet(receivers=valid_emails, subject=subject, mail_body=mail_body, from_email=from_email)

    def send_via_smtp(self, receivers, subject, mail_body, from_email):
        AppLogger.print("Sending with SMTP", )
        try:
            message = send_mail(
                from_email=from_email,
                recipient_list=receivers,
                subject=subject,
                html_message=mail_body,
                message=""
            )

            return message, None

        except Exception as e:
            AppLogger.report(self, error=e)
            return None, e

    def send_via_mailjet(self, receivers, subject, mail_body, from_email):
        AppLogger.print("Sending with MailJet", )
        mailjet_api_key = settings.MJ_API_KEY
        mailjet_api_secret = settings.MJ_API_SECRET

        data = {
            'Messages': [
                {
                    "From": {
                        "Email": from_email,
                        "Name": settings.APP_INFO_DEFAULTS.get("app_name"),
                    },
                    "To": [{"Email": email} for email in receivers],
                    "Subject": subject,
                    "HTMLPart": mail_body
                }
            ]
        }

        try:
            mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret), version='v3.1')
            message_sent = mailjet.send.create(data=data)

            return message_sent, None

        except Exception as e:
            AppLogger.report(self, e)
            return None, e


def get_notification_template_for(message_type, is_refresh=False):
    message_data = notifications.get(message_type)
    if not message_data:
        return None

    template, is_created = MessageTemplate.objects.get_or_create(
        type=message_type
    )

    if is_created or is_refresh:
        message_content = ""
        try:
            if message_data.get("file"):
                file = message_data.get("file")
                file = file if file else "general_notification.html"
                module_dir = os.path.dirname(__file__)  # get current directory
                filename = os.path.join(module_dir, "notification_templates", file)

                try:
                    with open(filename) as file:
                        message_content = "".join(file.readlines())
                except:
                    message_content = ""
        except:
            message_content = ""

        message_subject = message_data.get("email_subject") or ''

        # in_app_message = message_data.get("in_app_message") or ''
        # push_message = message_data.get("push_message") or ''
        sms_message = message_data.get("sms_message") or ''

        template.email_template = message_content
        template.email_subject = message_subject

        # template.in_app_message = in_app_message
        # template.push_message = push_message
        template.sms_message = sms_message

        template.description = message_data.get("description")
        template.save()

        variables = message_data.get("variables")
        ids = []

        for variable in variables:
            variable_name = variable.get("name")
            variable_desc = variable.get("description")
            var, _ = MessageVariable.objects.update_or_create(
                name=variable_name,
                template=template,
                defaults={
                    "description": variable_desc
                }
            )
            ids.append(var.pk)

        MessageVariable.objects.filter(template=template).exclude(pk__in=ids).delete()

    return template


def render_to_template(string, data):
    context = Context(data)
    template = Template(string)

    return template.render(context)
