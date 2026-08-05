from core.celery import app
from utils.constants import CeleryTaskQueue
# from utils.third_party_connection import TermiiAPIService
from utils.service import format_otp, AppLogger
from .util import NotificationUtil
from .models import MessageTypes, NotificationType


@app.task(queue=CeleryTaskQueue.notification)
def send_password_reset(phone_number_or_email, otp, send_to=NotificationType.email):
    util = NotificationUtil(notification_type=send_to)

    otp = format_otp(otp)

    return util.send_notification(
        recipients=[phone_number_or_email],
        message_type=MessageTypes.password_reset,
        data={
            "otp": otp
        }
    )


@app.task(queue=CeleryTaskQueue.notification)
def send_dynamic_notification(recipients, username, message, send_to=NotificationType.email):
    util = NotificationUtil(notification_type=send_to)

    util.send_notification(
        recipients=recipients,
        message_type=MessageTypes.dynamic_notification,
        data={
            "username": username,
            "message": message
        }
    )


# @app.task(queue=CeleryTaskQueue.notification)
# def send_sms_notification(recipients, message):
#     termii_api_service = TermiiAPIService()
#     termii_api_service.send_sms_notification(recipients, message)


@app.task(queue=CeleryTaskQueue.notification)
def send_2fa_otp(phone_number_or_email, otp, first_name, send_to=NotificationType.email):
    util = NotificationUtil(notification_type=send_to)

    otp = format_otp(otp)

    return util.send_notification(
        recipients=[phone_number_or_email],
        message_type=MessageTypes.send_2fa_otp,
        data={
            "first_name": first_name,
            "otp": otp
        }
    )