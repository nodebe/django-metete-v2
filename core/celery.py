from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
from django.apps import apps
from django.conf import settings
from kombu import Queue
from utils.constants import CeleryTaskQueue

# --> celery -A core worker -l info -B
# --> celery -A core worker -l info -Q default -c 4 -n default
# --> celery -A core worker -l info -Q default -c 4 -n notification
# --> celery -A core worker -l info -Q default -c 4 -n logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core', broker=settings.BROKER_URL)

app.conf.queues = (
    Queue(CeleryTaskQueue.notification),
    Queue(CeleryTaskQueue.logging),
    Queue(CeleryTaskQueue.default),
)

app.conf.task_default_queue = CeleryTaskQueue.default
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {}
