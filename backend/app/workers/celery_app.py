import os
from celery import Celery
from .beat_config import BEAT_SCHEDULE, BEAT_TIMEZONE

broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
backend_url = os.getenv("REDIS_URL", "redis://redis:6379/1")

celery = Celery("insighthub", broker=broker_url, backend=backend_url)

# 태스크 라우팅 설정
celery.conf.task_routes = {
    "backend.app.workers.tasks.*": {"queue": "default"},
    "backend.app.workers.scheduled_tasks.*": {"queue": "rss_ingestion"},
}

# Celery Beat 설정
celery.conf.beat_schedule = BEAT_SCHEDULE
celery.conf.timezone = BEAT_TIMEZONE

# 태스크 등록
celery.autodiscover_tasks(['backend.app.workers'])

# 태스크 수동 등록
from . import tasks, scheduled_tasks
