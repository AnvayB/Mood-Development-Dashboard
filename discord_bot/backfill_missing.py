"""
One-time backfill: insert the two mood entries that were dropped by the
pending-notes expiry bug on May 23 and May 25, 2026.

Run from the discord_bot/ directory with credentials in .env:
    python backfill_missing.py
"""
from datetime import date
from database import insert_entry, entry_exists

MISSING = [
    (date(2026, 5, 23), "Tired"),
    (date(2026, 5, 25), "Happy"),
]

for log_date, emotion in MISSING:
    if entry_exists(log_date):
        print(f"  {log_date} already exists — skipping")
    else:
        insert_entry(log_date, emotion)
        print(f"  Inserted {emotion} for {log_date} ✓")

print("Done.")
