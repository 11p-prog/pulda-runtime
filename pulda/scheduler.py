from apscheduler.schedulers.background import BackgroundScheduler
from .config import settings
from .service import build_review, audit
from .connectors import sync_notion, sync_github, pull_notion_daily_activities

scheduler = BackgroundScheduler(timezone=settings.timezone)

def daily_cycle():
    try:
        build_review()
        if settings.auto_sync_notion:
            sync_notion()
        if settings.auto_sync_github:
            sync_github()
    except Exception as e:
        audit("daily_cycle", "scheduler", "failed", str(e))

def daily_activity_queue_cycle():
    try:
        pull_notion_daily_activities()
    except Exception as e:
        audit("daily_activity_queue_cycle", "scheduler", "failed", str(e))

def start_scheduler():
    if settings.auto_review and not scheduler.running:
        scheduler.add_job(
            daily_cycle, "cron",
            hour=settings.review_hour, minute=settings.review_minute,
            id="daily_cycle", replace_existing=True,
        )
        if settings.auto_ingest_daily_activity_queue:
            scheduler.add_job(
                daily_activity_queue_cycle, "cron",
                hour=settings.daily_activity_pull_hour,
                minute=settings.daily_activity_pull_minute,
                id="daily_activity_queue_cycle", replace_existing=True,
            )
        scheduler.start()
