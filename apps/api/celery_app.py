"""
Celery application configuration for background tasks.
"""
from celery import Celery
from config import get_config

config = get_config()

# Initialize Celery
celery = Celery(
    'takeabreak',
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
    include=[
        'app.tasks.calendar_tasks',
    ]
)

# Configure Celery
celery.conf.update(
    timezone='UTC',
    enable_utc=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery.conf.beat_schedule = {
    'sync-all-calendars': {
        'task': 'sync_all_users_calendars',
        'schedule': 3600.0,  # Every hour
    },
    'generate-daily-recommendations': {
        'task': 'generate_daily_recommendations',
        'schedule': 86400.0,  # Every day at midnight
    },
    'cleanup-old-events': {
        'task': 'cleanup_old_calendar_events',
        'schedule': 86400.0,  # Daily cleanup
    },
    'refresh-expired-tokens': {
        'task': 'refresh_expired_tokens',
        'schedule': 1800.0,  # Every 30 minutes
    },
}

celery.conf.timezone = 'UTC'

if __name__ == '__main__':
    celery.start()