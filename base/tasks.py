from django.conf import settings
from base.models import ApiRequestLogger, Activity
from core.celery import app
from utils.constants import CeleryTaskQueue


def make_api_request_log(user_id, request_data, request_path, ref_id, headers):
    if isinstance(request_data, dict):
        request_data = {k: "****" if k in settings.SENSITIVE_KEYS else v for k, v in request_data.items()}

    ApiRequestLogger.objects.create(
        user_id=user_id,
        path=request_path,
        headers=headers,
        request_data=request_data,
        ref_id=ref_id
    )


@app.task(queue=CeleryTaskQueue.logging)
def update_api_request_log(ref_id, response_status, response_body):
    request_log = ApiRequestLogger.objects.filter(ref_id=ref_id).first()

    data = response_body.get("data")

    if isinstance(data, dict):
        response_body = {k: "****" if k in settings.SENSITIVE_KEYS else v for k, v in response_body.get("data").items()}

    if request_log:
        request_log.status = response_status
        request_log.response_body = response_body
        request_log.save()


@app.task(queue=CeleryTaskQueue.logging)
def report_activity(user_id, activity_type, description, data):
    Activity.objects.create(
        user_id=user_id,
        activity_type=activity_type,
        note=description,
        data=data
    )
