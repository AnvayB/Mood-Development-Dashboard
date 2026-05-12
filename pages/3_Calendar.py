import html as html_lib
import re
import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import date
from data.db import load_all_entries

MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"]

st.markdown(
    """
    <style>
    .block-container {
        max-width: 75vw !important;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }
    div[data-testid="stHorizontalBlock"]:has(select) {
        align-items: center;
    }
    .stMultiSelect > div > div > div.st-ak.st-al.st-bc.st-bd.st-be {
        width: 60px !important;
    }
    .stMultiSelect > div.st-ae[data-baseweb="select"] {
        width: 200px !important;
        height: 40px !important;
        min-height: 40px !important;
        max-height: 40px !important;
    }
    .day-cell { position: relative; overflow: visible; }
    .day-note-wrapper { position: absolute; bottom: 6px; right: 8px; overflow: visible; }
    .day-note-icon { cursor: default; opacity: 0.55; font-size: 13px; line-height: 1; display: block; }
    .day-note-tooltip {
        visibility: hidden; opacity: 0;
        position: absolute; bottom: 22px; right: 0;
        background: rgba(18,18,18,0.97); color: #f0f0f0;
        padding: 8px 10px; border-radius: 8px;
        font-size: 11px; line-height: 1.45; width: 170px;
        white-space: normal; z-index: 9999;
        transition: opacity 0.15s ease;
        border: 1px solid rgba(255,255,255,0.13);
        box-shadow: 0 4px 18px rgba(0,0,0,0.55);
        pointer-events: none;
    }
    .day-note-wrapper:hover .day-note-tooltip { visibility: visible; opacity: 1; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_all():
    return load_all_entries()

df = load_all()

st.title("Calendar")

# ----------------------------
# Sidebar: year/month selection
# ----------------------------
years = sorted(df["year"].unique().tolist())
year = st.sidebar.selectbox("Year", years, index=len(years) - 1)

months_available = sorted(df[df["year"] == year]["month"].unique().tolist())
default_month_idx = len(months_available) - 1
month = st.sidebar.selectbox(
    "Month",
    months_available,
    index=default_month_idx,
    format_func=lambda m: MONTH_NAMES[m-1],
)

# Emotions list (used later for filter)
emotions = sorted(df["emotion"].dropna().unique().tolist())

# ----------------------------
# Build month data
# ----------------------------
dfm = df[(df["year"] == year) & (df["month"] == month)].copy()
dfm = dfm.sort_values("day")

day_to_row = {int(r["day"]): r for _, r in dfm.iterrows()}

# ----------------------------
# Color mapping
# ----------------------------
EMOTION_HEX = {
    "Happy": "#FFD966",
    "Productive": "#38761D",
    "Good": "#93C47D",
    "Tired": "#9FC5E8",
    "Lazy": "#EAD1DC",
    "SAD": "#B7B7B7",
    "Stress/Anxiety": "#D1802C",
    "Angry/Annoyed": "#CC0000",
    "Depressed": "#1155CC",
    "Hopeless": "#674EA7",
    "Horrible": "#000000",
    "Suicidal": "#000000",
}

def text_color(bg_hex: str) -> str:
    h = bg_hex.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    lum = 0.2126*r + 0.7152*g + 0.0722*b
    return "#111111" if lum > 160 else "#F5F5F5"

def clean_note(raw) -> str:
    """Return plain text from a notes value (strip HTML tags the DB may have stored)."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return ""
    return re.sub(r"<[^>]+>", "", str(raw)).strip()

# ----------------------------
# Calendar grid
# ----------------------------
st.subheader(f"{MONTH_NAMES[month-1]} {year}")

cal = calendar.Calendar(firstweekday=6)  # 6 = Sunday
weeks = cal.monthdayscalendar(year, month)

cols = st.columns(7)
for i, name in enumerate(["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]):
    cols[i].markdown(
        f"<div style='text-align:center;opacity:0.8;font-weight:600;'>{name}</div>",
        unsafe_allow_html=True
    )

for week in weeks:
    cols = st.columns(7)
    for i, d in enumerate(week):
        if d == 0:
            cols[i].markdown(
                "<div style='height:78px;border-radius:12px;background:rgba(255,255,255,0.03);'></div>",
                unsafe_allow_html=True
            )
            continue

        row = day_to_row.get(d)
        if row is None:
            cols[i].markdown(
                f"<div style='height:78px;border-radius:12px;padding:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);'>"
                f"<div style='font-size:16px;font-weight:700;'>{d}</div>"
                f"<div style='opacity:0.6;font-size:12px;'>No data</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            continue

        emo = str(row["emotion"])
        score = row["score"]
        bg = EMOTION_HEX.get(emo, "#444444")
        fg = text_color(bg)

        # Build note tooltip — strip any HTML the DB may have stored, then escape
        note_text = clean_note(row.get("notes", None))
        note_html = ""
        if note_text:
            safe = html_lib.escape(note_text)
            note_html = (
                '<div class="day-note-wrapper">'
                '<span class="day-note-icon">\U0001f4c4</span>'
                f'<div class="day-note-tooltip">{safe}</div>'
                '</div>'
            )

        score_display = int(score) if pd.notna(score) else ""
        # Single-string cell — avoids Streamlit markdown parser mangling newlines
        cell = (
            f'<div class="day-cell" style="height:78px;border-radius:14px;padding:10px;'
            f'background:{bg};color:{fg};border:1px solid rgba(255,255,255,0.12);'
            f'box-shadow:0 8px 30px rgba(0,0,0,0.25);">'
            f'<div style="font-size:16px;font-weight:800;line-height:1;">{d}</div>'
            f'<div style="margin-top:6px;font-size:12px;font-weight:600;opacity:0.95;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{html_lib.escape(emo)}</div>'
            f'<div style="margin-top:2px;font-size:12px;opacity:0.9;">{score_display}</div>'
            f'{note_html}'
            f'</div>'
        )
        cols[i].markdown(cell, unsafe_allow_html=True)

st.divider()

# ----------------------------
# Month table (drill-down)
# ----------------------------
header_col1, header_col2 = st.columns([1, 0.15])
with header_col1:
    st.subheader("Daily log (this month)")
with header_col2:
    emotion_filter = st.multiselect(
        "Filter table to emotion(s)",
        emotions,
        default=[],
        label_visibility="collapsed",
        key="emotion_filter"
    )

table = dfm.copy()
table["date"] = table["date"].dt.date

if emotion_filter:
    table = table[table["emotion"].isin(emotion_filter)]

table_cols = ["date", "day", "emotion", "score", "sheet", "color_hex"]
if "notes" in table.columns:
    table_cols.append("notes")
st.dataframe(
    table[table_cols],
    use_container_width=True,
    hide_index=True
)

# quick summary row
c1, c2, c3 = st.columns(3)
c1.metric("Days in view", int(table["date"].nunique()))
c2.metric("Avg score", round(float(table["score"].mean()), 2) if len(table) else 0)
if len(table):
    best = table.loc[table["score"].idxmax()]
    c3.metric("Best day", str(best["date"]), int(best["score"]))
else:
    c3.metric("Best day", "-", "-")
