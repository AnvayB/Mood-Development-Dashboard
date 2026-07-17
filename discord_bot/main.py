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
        log_date, expiry = pending_notes.pop(uid)
        if time.time() < expiry and text.lower() not in {"no", "nope", "n", "skip", "nah"}:
            db.update_notes(log_date, text)
            await message.channel.send("Note saved ✓")
        else:
            await message.channel.send("No worries, see you tomorrow!")
        return

    # Check for a pending session (supports late replies)
    session = db.get_pending_session(settings.DISCORD_USER_ID)
    log_date = date.fromisoformat(session["for_date"]) if session else _today_pt()

    # Duplicate guard
    if db.entry_exists(log_date):
        await message.channel.send(f"You already logged {log_date.strftime('%b %d')} ✓")
        return

    # Match input to a valid emotion (case-insensitive, with synonyms)
    SYNONYMS: dict[str, str] = {
        # Happy
        "happy": "Happy", "happiness": "Happy", "great": "Happy", "amazing": "Happy",
        "wonderful": "Happy", "joyful": "Happy", "excited": "Happy", "elated": "Happy",
        "fantastic": "Happy", "awesome": "Happy", "ecstatic": "Happy", "cheerful": "Happy",
        "thrilled": "Happy", "delighted": "Happy", "pleased": "Happy",
        # Productive
        "productive": "Productive", "productive day": "Productive", "accomplished": "Productive",
        "focused": "Productive", "motivated": "Productive", "efficient": "Productive", "busy": "Productive",
        # Good
        "good": "Good", "okay": "Good", "ok": "Good", "fine": "Good", "alright": "Good",
        "decent": "Good", "not bad": "Good", "pretty good": "Good", "solid": "Good",
        # Tired
        "tired": "Tired", "exhausted": "Tired", "sleepy": "Tired", "fatigued": "Tired",
        "fatigue": "Tired", "drained": "Tired", "worn out": "Tired", "drowsy": "Tired",
        "sluggish": "Tired", "worn-out": "Tired",
        # Lazy
        "lazy": "Lazy", "lethargic": "Lazy", "unmotivated": "Lazy", "unproductive": "Lazy",
        "bored": "Lazy", "procrastinating": "Lazy",
        # SAD
        "sad": "SAD", "unhappy": "SAD", "upset": "SAD", "down": "SAD", "blue": "SAD",
        "gloomy": "SAD", "melancholy": "SAD", "sorrowful": "SAD", "heartbroken": "SAD",
        "miserable": "SAD",
        # Stress/Anxiety
        "stress/anxiety": "Stress/Anxiety", "stressed": "Stress/Anxiety", "stressful": "Stress/Anxiety",
        "anxious": "Stress/Anxiety", "anxiety": "Stress/Anxiety", "nervous": "Stress/Anxiety",
        "overwhelmed": "Stress/Anxiety", "worried": "Stress/Anxiety", "tense": "Stress/Anxiety",
        "uneasy": "Stress/Anxiety", "panicked": "Stress/Anxiety", "stress": "Stress/Anxiety",
        # Angry/Annoyed
        "angry/annoyed": "Angry/Annoyed", "angry": "Angry/Annoyed", "annoyed": "Angry/Annoyed",
        "mad": "Angry/Annoyed", "frustrated": "Angry/Annoyed", "irritated": "Angry/Annoyed",
        "furious": "Angry/Annoyed", "agitated": "Angry/Annoyed", "pissed": "Angry/Annoyed",
        "rage": "Angry/Annoyed", "anger": "Angry/Annoyed",
        # Depressed
        "depressed": "Depressed", "depression": "Depressed", "empty": "Depressed",
        "numb": "Depressed", "worthless": "Depressed", "low": "Depressed",
        # Hopeless
        "hopeless": "Hopeless", "hopelessness": "Hopeless", "defeated": "Hopeless",
        "despair": "Hopeless", "despairing": "Hopeless", "giving up": "Hopeless",
        # Suicidal
        "suicidal": "Suicidal",
    }
    emotion = SYNONYMS.get(text.lower())
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

    pending_notes[str(message.author.id)] = (log_date, time.time() + 3600)
    await message.channel.send(
        "Want to add a note for today? Reply with anything you want to remember, or 'no' to skip 📝"
    )


bot.run(settings.DISCORD_BOT_TOKEN)
