import time
from datetime import date, datetime

import discord
import pytz

import database as db
from config import settings
from database import EMOTION_MAP
from scheduler import _today_pt, schedule_daily_prompt

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# Maps Discord user_id -> (log_date, expiry_unix_timestamp)
# Tracks users awaiting a follow-up notes reply after mood logging.
pending_notes: dict[str, tuple[date, float]] = {}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    user = await bot.fetch_user(int(settings.DISCORD_USER_ID))
    await user.send("✅ Mood bot is online! I'll DM you every night at 9pm PT to log your day.")
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

    # Handle pending notes reply (must come before mood-logging logic)
    uid = str(message.author.id)
    if uid in pending_notes:
        log_date, expiry = pending_notes[uid]
        if time.time() < expiry:
            # Still within the notes window — treat this as a notes reply
            pending_notes.pop(uid)
            if text.lower() not in {"no", "nope", "n", "skip", "nah"}:
                db.update_notes(log_date, text)
                await message.channel.send("Note saved ✓")
            else:
                await message.channel.send("No worries, see you tomorrow!")
            return
        else:
            # Expired — discard the stale entry and fall through to mood logging
            pending_notes.pop(uid)

    # Check for a pending session (supports late replies)
    session = db.get_pending_session(settings.DISCORD_USER_ID)
    log_date = date.fromisoformat(session["for_date"]) if session else _today_pt()

    # Duplicate guard — also clean up any stale session so it doesn't haunt future messages
    if db.entry_exists(log_date):
        if session:
            db.mark_session_responded(session["id"])
        await message.channel.send(f"You already logged {log_date.strftime('%b %d')} ✓")
        return

    # Match input to a valid emotion (case-insensitive)
    emotion_lookup = {k.lower(): k for k in EMOTION_MAP}
    emotion = emotion_lookup.get(text.lower())
    if emotion is None:
        valid = ", ".join(EMOTION_MAP.keys())
        await message.channel.send(f"Hmm, I didn't recognize that. Valid emotions: {valid}")
        return

    # Persist to Supabase
    db.insert_entry(log_date, emotion)
    if session:
        db.mark_session_responded(session["id"])

    score = EMOTION_MAP[emotion]["score"]
    await message.channel.send(
        f"Logged: {emotion} ({score}/11) for {log_date.strftime('%a %b %-d')} ✓"
    )

    pending_notes[str(message.author.id)] = (log_date, time.time() + 8 * 3600)
    await message.channel.send(
        "Want to add a note for today? Reply with anything you want to remember, or 'no' to skip 📝"
    )


bot.run(settings.DISCORD_BOT_TOKEN)
