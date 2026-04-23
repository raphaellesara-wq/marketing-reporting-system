from celery import Celery
from app.config import settings

celery_app = Celery(
    "marketing_reporting",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "daily-reports": {
            "task": "app.tasks.run_scheduled_reports",
            "schedule": 86400,  # every 24h
        },
    },
)
