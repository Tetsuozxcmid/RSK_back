from celery import Celery
from celery.schedules import crontab
from app.config import settings


celery_app = Celery(
    "learning_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.learning_tasks"],
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
)


celery_app.conf.beat_schedule = {
    # Старая задача (для совместимости, запуск в 3 часа ночи)
    "update-learning-status-every-day": {
        "task": "app.services.learning_tasks.update_all_users_learning_status",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "learning"},
    },
    # НОВАЯ задача - каждый час!
    "update-learning-statuses-every-hour": {
        "task": "services.learning_tasks.update_learning_statuses",  # ВАЖНО: правильный путь!
        "schedule": crontab(minute=0),  # Каждый час в 00 минут
        "options": {"queue": "learning"},
    },
}