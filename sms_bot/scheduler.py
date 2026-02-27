from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from twilio.rest import Client

import database as db
from config import settings


def send_daily_prompt() -> None:
    twilio = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    twilio.messages.create(
        body="Hey! How was your day? Reply with how you felt and I'll log it for you 📝",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=settings.MY_PHONE_NUMBER,
    )
    db.log_pending_session(settings.MY_PHONE_NUMBER, date.today())
    print(f"Daily prompt sent for {date.today()}")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_daily_prompt,
        CronTrigger(hour=21, minute=0, timezone="America/Los_Angeles"),
    )
    scheduler.start()
    print("Scheduler started — daily prompt fires at 9pm PT")
    return scheduler
