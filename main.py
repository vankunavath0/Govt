import os
import time
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from database import init_db, is_job_seen, mark_job_seen
from scraper import run_all_scrapers
from bot import send_telegram_alert

load_dotenv()
logger = logging.getLogger(__name__)

def job_execution_cycle():
    logger.info("Starting scheduled job discovery cycle...")
    jobs = run_all_scrapers()
    new_jobs_count = 0

    for job in jobs:
        url = job.get("app_link")
        if not url or is_job_seen(url):
            continue

        if send_telegram_alert(job):
            mark_job_seen(url, job.get("org_name", ""), job.get("role_name", ""))
            new_jobs_count += 1
            time.sleep(1.5)  # Rate limiting to respect Telegram API quotas

    logger.info(f"Cycle completed. {new_jobs_count} new alerts broadcasted.")

if __name__ == "__main__":
    init_db()
    
    # Run once immediately on startup
    job_execution_cycle()

    # Configure daily scheduler
    tz_name = os.getenv("TIMEZONE", "Asia/Kolkata")
    timezone = pytz.timezone(tz_name)
    hour = int(os.getenv("SCHEDULE_HOUR", 8))
    minute = int(os.getenv("SCHEDULE_MINUTE", 0))

    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(
        job_execution_cycle,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="daily_job_alerts",
        name="Daily Job Alert Scraper",
        replace_existing=True
    )

    logger.info(f"Scheduler active: daily at {hour:02d}:{minute:02d} ({tz_name}).")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutting down gracefully.")