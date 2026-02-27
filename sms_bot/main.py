from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse

import database as db
import scheduler as sched
from categorize import categorize_emotion
from database import EMOTION_MAP


@asynccontextmanager
async def lifespan(app: FastAPI):
    sched.start_scheduler()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhook/sms", response_class=PlainTextResponse)
async def handle_sms(Body: str = Form(), From: str = Form()):
    resp = MessagingResponse()
    text = Body.strip()

    # Which date to log for — use the date the prompt was sent (supports late replies)
    session = db.get_pending_session(From)
    log_date = date.fromisoformat(session["for_date"]) if session else date.today()

    # Duplicate guard
    if db.entry_exists(log_date):
        resp.message(f"You already logged {log_date.strftime('%b %d')} ✓")
        return str(resp)

    # Categorize with Claude
    emotion = categorize_emotion(text)

    # Persist to Supabase
    db.insert_entry(log_date, emotion)
    if session:
        db.mark_session_responded(session["id"])

    score = EMOTION_MAP[emotion]["score"]
    resp.message(
        f"Logged: {emotion} ({score}/11) for {log_date.strftime('%a %b %-d')} ✓"
    )
    return str(resp)


@app.get("/health")
def health():
    return {"status": "ok"}
