from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ebomboleadmanager",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.verification", "app.tasks.enrichment", "app.tasks.linkedin", "app.tasks.pipeline"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Process one task at a time
)


def parse_cron_schedule(schedule_str: str) -> dict:
    """Parse a cron string into celery crontab kwargs."""
    parts = schedule_str.split()
    if len(parts) != 5:
        # Default: daily at 8 AM
        return {"hour": 8, "minute": 0}

    return {
        "minute": parts[0],
        "hour": parts[1],
        "day_of_month": parts[2],
        "month_of_year": parts[3],
        "day_of_week": parts[4],
    }


# Configure Celery Beat schedule for LinkedIn scraping
if settings.linkedin_username and settings.linkedin_password:
    cron_kwargs = parse_cron_schedule(settings.linkedin_scrape_schedule)
    celery_app.conf.beat_schedule = {
        "scheduled-linkedin-scrape": {
            "task": "app.tasks.linkedin.scheduled_linkedin_scrape",
            "schedule": crontab(**cron_kwargs),
        },
    }
