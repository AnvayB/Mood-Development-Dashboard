import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    df_all = pd.read_csv("data/mood_all_years.csv", parse_dates=["date"])
    df_monthly = pd.read_csv("data/mood_monthly_hi.csv")
    df_year_emotion = pd.read_csv("data/mood_year_emotion_breakdown.csv")

    # Normalize dtypes
    for c in ["year", "month", "day", "score"]:
        if c in df_all.columns:
            df_all[c] = pd.to_numeric(df_all[c], errors="coerce")

    for c in ["year", "month", "happiness_index"]:
        if c in df_monthly.columns:
            df_monthly[c] = pd.to_numeric(df_monthly[c], errors="coerce")

    # If your yearly breakdown has pct_days
    if "pct_days" in df_year_emotion.columns:
        df_year_emotion["pct_days"] = pd.to_numeric(df_year_emotion["pct_days"], errors="coerce")

    return df_all, df_monthly, df_year_emotion
