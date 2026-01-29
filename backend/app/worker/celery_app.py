from celery import Celery
from backend.app.core.config import settings

# Initialize Celery
# Default to Redis if CELERY_BROKER_URL is not set
broker_url = settings.CELERY_BROKER_URL or str(settings.REDIS_URL)

celery_app = Celery(
    "ajax_worker",
    broker=broker_url,
    backend=settings.CELERY_RESULT_BACKEND or broker_url
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Clean Architecture: Autodiscover tasks in the worker package
    imports=["backend.app.worker.tasks"],
    # Schedule: Run sub cleanup every day at midnight
    beat_schedule={
        "cleanup-expired-subs-every-midnight": {
            "task": "tasks.cleanup_expired_subscriptions",
            "schedule": 86400.0, # Every 24 hours (86400 seconds)
        },
    }
)

if __name__ == "__main__":
    celery_app.start()
