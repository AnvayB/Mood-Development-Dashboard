from datetime import date

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import database as db
from config import settings


async def send_daily_prompt(bot: discord.Client) -> None:
    user = await bot.fetch_user(int(settings.DISCORD_USER_ID))
    await user.send("Hey! How was your day? Reply with how you felt and I'll log it for you 📝")
    db.log_pending_session(settings.DISCORD_USER_ID, date.today())
    print(f"Daily prompt sent for {date.today()}")


def schedule_daily_prompt(bot: discord.Client) -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_prompt,
        CronTrigger(hour=21, minute=0, timezone="America/Los_Angeles"),
        args=[bot],
    )
    scheduler.start()
    print("Scheduler started — daily prompt fires at 9pm PT")
