"""
One-time migration: load mood_all_years.csv → Supabase mood_entries table.

Run from the repo root:
    SUPABASE_URL=... SUPABASE_KEY=... python sms_bot/migrate.py
"""
import math
import os
import sys

import pandas as pd
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_KEY env vars before running.")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mood_all_years.csv")
df = pd.read_csv(CSV_PATH, parse_dates=["date"])
df["date"] = df["date"].dt.date.astype(str)
df["match_dist"] = df["match_dist"].apply(
    lambda x: 0.0 if (x is None or (isinstance(x, float) and math.isnan(x))) else float(x)
)

cols = ["date", "year", "month", "day", "sheet", "emotion", "score",
        "color_hex", "palette_match", "match_dist"]
records = df[cols].to_dict(orient="records")

BATCH = 100
print(f"Migrating {len(records)} rows to Supabase...")
for i in range(0, len(records), BATCH):
    batch = records[i:i + BATCH]
    client.table("mood_entries").upsert(batch, on_conflict="date").execute()
    print(f"  {min(i + BATCH, len(records))}/{len(records)} rows done")

print("Migration complete!")
