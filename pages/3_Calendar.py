import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import date

MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"]

st.markdown(
    """
    <style>
    .block-container {
        max-width: 75vw !important;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }
    /* Style the inline emotion selectbox to look more integrated */
    div[data-testid="stHorizontalBlock"]:has(select) {
        align-items: center;
    }
    /* Style the multiselect filter width - target the value display container */
    .stMultiSelect > div > div > div.st-ak.st-al.st-bc.st-bd.st-be {
        width: 60px !important;
    }
    /* Target the main multiselect container - set width to 200px and lock height */
    .stMultiSelect > div.st-ae[data-baseweb="select"] {
        width: 200px !important;
        height: 40px !important;
        min-height: 40px !important;
        max-height: 40px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



@st.cache_data
def load_all():
    df = pd.read_csv("data/mood_all_years.csv", parse_dates=["date"])
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["day"] = df["day"].astype(int)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    return df

df = load_all()

st.title("Calendar")

# ----------------------------
# Sidebar: year/month selection
# ----------------------------
years = sorted(df["year"].unique().tolist())
year = st.sidebar.selectbox("Year", years, index=len(years) - 1)

months_available = sorted(df[df["year"] == year]["month"].unique().tolist())
# default to latest available month in that year
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

# one row per day (you should already have 1/day)
day_to_row = {int(r["day"]): r for _, r in dfm.iterrows()}

# ----------------------------
# Color mapping (use your palette_match if you want, but emotion is enough)
# Feel free to tweak the hex values to match your actual sheet colors.
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
    # If you have extras (like you showed earlier)
    "Suicidal": "#000000",
}

def text_color(bg_hex: str) -> str:
    """Choose white/black text based on background luminance."""
    h = bg_hex.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    # perceived luminance
    lum = 0.2126*r + 0.7152*g + 0.0722*b
    return "#111111" if lum > 160 else "#F5F5F5"

# ----------------------------
# Calendar grid (Mon-Sun)
# ----------------------------
st.subheader(f"{MONTH_NAMES[month-1]} {year}")

cal = calendar.Calendar(firstweekday=0)  # 0=Monday
weeks = cal.monthdayscalendar(year, month)

# Weekday labels
cols = st.columns(7)
for i, name in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
    cols[i].markdown(f"<div style='text-align:center; opacity:0.8; font-weight:600;'>{name}</div>", unsafe_allow_html=True)

# Render each week
for week in weeks:
    cols = st.columns(7)
    for i, d in enumerate(week):
        if d == 0:
            # empty cell
            cols[i].markdown(
                "<div style='height:78px; border-radius:12px; background:rgba(255,255,255,0.03);'></div>",
                unsafe_allow_html=True
            )
            continue

        row = day_to_row.get(d)
        if row is None:
            # missing day (should be rare)
            cols[i].markdown(
                f"<div style='height:78px; border-radius:12px; padding:10px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06);'>"
                f"<div style='font-size:16px; font-weight:700;'>{d}</div>"
                f"<div style='opacity:0.6; font-size:12px;'>No data</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            continue

        emo = str(row["emotion"])
        score = row["score"]
        bg = EMOTION_HEX.get(emo, "#444444")
        fg = text_color(bg)

        # Tooltip via title=""
        tooltip = f"{emo} | score {score} | {row['date'].date()}"

        cols[i].markdown(
            f"""
            <div title="{tooltip}"
                 style="
                    height:78px;
                    border-radius:14px;
                    padding:10px;
                    background:{bg};
                    color:{fg};
                    border:1px solid rgba(255,255,255,0.12);
                    box-shadow: 0 8px 30px rgba(0,0,0,0.25);
                 ">
                <div style="font-size:16px; font-weight:800; line-height:1;">{d}</div>
                <div style="margin-top:6px; font-size:12px; font-weight:600; opacity:0.95; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {emo}
                </div>
                <div style="margin-top:2px; font-size:12px; opacity:0.9;">
                    {int(score) if pd.notna(score) else ""}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.divider()

# ----------------------------
# Month table (drill-down)
# ----------------------------
# Create inline subheader with filter
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

st.dataframe(
    table[["date","day","emotion","score","sheet","color_hex"]],
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
