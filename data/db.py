"""
Shared Supabase data helpers for all Streamlit pages.
Replaces pd.read_csv("data/mood_all_years.csv") and pd.read_csv("data/mood_monthly_hi.csv").
"""
import calendar as cal

import pandas as pd
import streamlit as st
from supabase import create_client

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_data(ttl=300)
def load_all_entries() -> pd.DataFrame:
    """Replaces pd.read_csv('data/mood_all_years.csv') across all pages.
    Cache refreshes every 5 minutes so new SMS entries appear promptly."""
    client = _client()
    rows = []
    chunk = 1000
    start = 0
    while True:
        batch = (
            client.table("mood_entries")
            .select("*")
            .order("date")
            .range(start, start + chunk - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < chunk:
            break
        start += chunk
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    # Derive year/month/day from date — ensures manual edits to `date` in
    # Supabase are always reflected correctly without needing to update all columns.
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["month_name"] = df["month"].map(lambda m: MONTH_NAMES[int(m) - 1])
    df["year_month"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str) + "-01"
    )
    return df


@st.cache_data(ttl=300)
def load_monthly_hi() -> pd.DataFrame:
    """Replaces pd.read_csv('data/mood_monthly_hi.csv').
    Computed on-the-fly from mood_entries: raw sum per month, then 30-day normalized
    (same logic as the existing per-page normalization)."""
    df = load_all_entries()
    monthly = (
        df.groupby(["year", "month"], as_index=False)["score"]
          .sum()
          .rename(columns={"score": "happiness_index"})
    )
    monthly["source_sheet"] = "computed"
    # 30-day normalization so month-length differences don't distort comparisons
    monthly["_actual_days"] = monthly.apply(
        lambda r: cal.monthrange(int(r["year"]), int(r["month"]))[1], axis=1
    )
    monthly["happiness_index"] = (
        monthly["happiness_index"] / monthly["_actual_days"] * 30
    ).round(0).astype("Int64")
    monthly.drop(columns=["_actual_days"], inplace=True)
    monthly["month_name"] = monthly["month"].map(lambda m: MONTH_NAMES[int(m) - 1])
    monthly["year_month"] = pd.to_datetime(
        monthly["year"].astype(str) + "-" + monthly["month"].astype(str) + "-01"
    )
    return monthly.dropna(subset=["happiness_index"]).copy()
