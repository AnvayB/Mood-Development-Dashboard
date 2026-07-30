from datetime import date

from supabase import create_client

from config import settings

client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

EMOTION_MAP = {
    "Happy":          {"score": 11, "color_hex": "#FFD966"},
    "Productive":     {"score": 10, "color_hex": "#38761D"},
    "Good":           {"score": 9,  "color_hex": "#93C47D"},
    "Tired":          {"score": 8,  "color_hex": "#9FC5E8"},
    "Lazy":           {"score": 7,  "color_hex": "#EAD1DC"},
    "SAD":            {"score": 6,  "color_hex": "#B7B7B7"},
    "Stress/Anxiety": {"score": 5,  "color_hex": "#D1802C"},
    "Angry/Annoyed":  {"score": 4,  "color_hex": "#CC0000"},
    "Depressed":      {"score": 3,  "color_hex": "#1155CC"},
    "Hopeless":       {"score": 2,  "color_hex": "#674EA7"},
    "Suicidal":       {"score": 1,  "color_hex": "#000000"},
}


def insert_entry(log_date: date, emotion: str) -> None:
    meta = EMOTION_MAP[emotion]
    client.table("mood_entries").insert({
        "date": log_date.isoformat(),
        "year": log_date.year,
        "month": log_date.month,
        "day": log_date.day,
        "sheet": "discord_bot",
        "emotion": emotion,
        "score": meta["score"],
        "color_hex": meta["color_hex"],
        "palette_match": "DISCORD_BOT",
        "match_dist": 0.0,
    }).execute()


def entry_exists(log_date: date) -> bool:
    res = (client.table("mood_entries")
           .select("id")
           .eq("date", log_date.isoformat())
           .execute())
    return len(res.data) > 0


def log_pending_session(phone: str, for_date: date) -> None:
    client.table("pending_sessions").insert({
        "phone_number": phone,
        "for_date": for_date.isoformat(),
    }).execute()


def get_pending_session(phone: str) -> dict | None:
    """Return the most recent unresponded session for this phone number."""
    res = (client.table("pending_sessions")
           .select("*")
           .eq("phone_number", phone)
           .eq("responded", False)
           .order("sent_at", desc=True)
           .limit(1)
           .execute())
    return res.data[0] if res.data else None


def mark_session_responded(session_id: int) -> None:
    (client.table("pending_sessions")
     .update({"responded": True})
     .eq("id", session_id)
     .execute())


def update_notes(log_date: date, notes: str) -> None:
    (client.table("mood_entries")
     .update({"notes": notes})
     .eq("date", log_date.isoformat())
     .execute())


def set_note_pending(log_date: date, expires_at: str) -> None:
    (client.table("mood_entries")
     .update({"note_pending": True, "note_expires_at": expires_at})
     .eq("date", log_date.isoformat())
     .execute())


def get_pending_note_date() -> date | None:
    res = (client.table("mood_entries")
           .select("date")
           .eq("note_pending", True)
           .gt("note_expires_at", "now()")
           .order("date", desc=True)
           .limit(1)
           .execute())
    return date.fromisoformat(res.data[0]["date"]) if res.data else None


def clear_note_pending(log_date: date) -> None:
    (client.table("mood_entries")
     .update({"note_pending": False, "note_expires_at": None})
     .eq("date", log_date.isoformat())
     .execute())
