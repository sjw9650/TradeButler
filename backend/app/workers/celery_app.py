import os
from celery import Celery

broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
backend_url = os.getenv("REDIS_URL", "redis://redis:6379/1")
celery = Celery("insighthub", broker=broker_url, backend=backend_url)
celery.conf.task_routes = {"tasks.*": {"queue": "default"}}

# 태스크 등록
celery.autodiscover_tasks(['backend.app.workers'])
