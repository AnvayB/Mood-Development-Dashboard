from datetime import date

import discord

import database as db
from categorize import categorize_emotion
from config import settings
from database import EMOTION_MAP
from scheduler import schedule_daily_prompt

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    schedule_daily_prompt(bot)


@bot.event
async def on_message(message: discord.Message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Only handle DMs from the configured user
    if not isinstance(message.channel, discord.DMChannel):
        return
    if str(message.author.id) != settings.DISCORD_USER_ID:
        return

    text = message.content.strip()

    # Check for a pending session (supports late replies)
    session = db.get_pending_session(settings.DISCORD_USER_ID)
    log_date = date.fromisoformat(session["for_date"]) if session else date.today()

    # Duplicate guard
    if db.entry_exists(log_date):
        await message.channel.send(f"You already logged {log_date.strftime('%b %d')} ✓")
        return

    # Categorize with Claude
    emotion = categorize_emotion(text)

    # Persist to Supabase
    db.insert_entry(log_date, emotion)
    if session:
        db.mark_session_responded(session["id"])

    score = EMOTION_MAP[emotion]["score"]
    await message.channel.send(
        f"Logged: {emotion} ({score}/11) for {log_date.strftime('%a %b %-d')} ✓"
    )


bot.run(settings.DISCORD_BOT_TOKEN)
