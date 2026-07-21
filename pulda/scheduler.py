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
    # 2026-07-21 / CR-0015: queue ingestion is an independent circulation job;
    # AUTO_REVIEW only controls review generation. Recovery: revert this commit.
    if not scheduler.running and (settings.auto_review or settings.auto_ingest_daily_activity_queue):
        if settings.auto_review:
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
