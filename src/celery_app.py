from celery import Celery
from celery.schedules import crontab
from src.config import settings

c_app = Celery(
    "url_shortener",
    broker=settings.CELERY_BROKER_URL,
    include=["src.tasks.purge"],
)
c_app.conf.timezone = "UTC"
# celery -A src.celery_app:c_app worker --loglevel=info --pool=solo

c_app.conf.beat_schedule = {
    "purge-expired-links": {
        "task": "purge_expired_links",
        "schedule": 30.0, # 30sec
        # "schedule": crontab(minute="0", hour="3", day_of_week="sunday") # run on every sunday at 3:00 UTC
    },
}
# celery -A src.celery_app:c_app beat --loglevel=info