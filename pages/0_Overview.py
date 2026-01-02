import calendar

import pandas as pd
import plotly.express as px
import streamlit as st

# Widen page content beyond default container
st.markdown(
    """
    <style>
    .block-container {
        max-width: 70vw !important;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }
    /* Disable the "app" link (first navigation item) in the sidebar */
    ul[data-testid="stSidebarNav"] > li:first-child a {
        pointer-events: none !important;
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data():
    df_all = pd.read_csv("data/mood_all_years.csv", parse_dates=["date"])
    df_monthly = pd.read_csv("data/mood_monthly_hi.csv")
    df_year_emotion = pd.read_csv("data/mood_year_emotion_breakdown.csv")

    for c in ["year", "month", "day", "score"]:
        if c in df_all.columns:
            df_all[c] = pd.to_numeric(df_all[c], errors="coerce")

    for c in ["year", "month", "happiness_index"]:
        if c in df_monthly.columns:
            df_monthly[c] = pd.to_numeric(df_monthly[c], errors="coerce")

    if "pct_days" in df_year_emotion.columns:
        df_year_emotion["pct_days"] = pd.to_numeric(df_year_emotion["pct_days"], errors="coerce")

    return df_all, df_monthly, df_year_emotion

df_all, df_monthly, df_year_emotion = load_data()

st.title("Overview")

years = sorted(df_all["year"].dropna().unique().astype(int))
default_year = years[-1] if years else None
year = st.sidebar.selectbox("Year", years, index=len(years)-1)

# Filter
dfy_all = df_all[df_all["year"] == year].copy()
dfy_monthly = df_monthly[df_monthly["year"] == year].copy().sort_values("month")

# Best month summary
best_month_value = "N/A"
worst_month_value = "N/A"
if not dfy_monthly.empty and dfy_monthly["happiness_index"].notna().any():
    best_month_idx = dfy_monthly["happiness_index"].idxmax()
    best_month_row = dfy_monthly.loc[best_month_idx]
    month_num = best_month_row.get("month")
    best_month_value = (
        calendar.month_abbr[int(month_num)] if pd.notna(month_num) else "Unknown"
    )
    worst_month_idx = dfy_monthly["happiness_index"].idxmin()
    worst_month_row = dfy_monthly.loc[worst_month_idx]
    worst_month_num = worst_month_row.get("month")
    worst_month_value = (
        calendar.month_abbr[int(worst_month_num)] if pd.notna(worst_month_num) else "Unknown"
    )

# KPIs
def emotion_for_score(score_value: int):
    """Return the most common emotion for a given rounded score."""
    if score_value is None:
        return None
    in_year = dfy_all[dfy_all["score"].round() == score_value]
    pool = in_year if not in_year.empty else df_all[df_all["score"].round() == score_value]
    if pool.empty or "emotion" not in pool.columns:
        return None
    return pool["emotion"].mode().iat[0]

avg_score_raw = dfy_all["score"].mean()
avg_score_rounded = int(round(avg_score_raw)) if pd.notna(avg_score_raw) else None
avg_emotion = emotion_for_score(avg_score_rounded) or "N/A"
avg_help = f"Rounded score: {avg_score_rounded}" if avg_score_rounded is not None else None

col1, col2, col3, col4 = st.columns(4)
col1.metric("Days logged", int(dfy_all["date"].nunique()))
col2.metric("Avg daily emotion", avg_emotion, help=avg_help)
col3.metric("Best month", best_month_value)
col4.metric("Worst month", worst_month_value)

st.divider()

# Monthly HI
fig = px.line(
    dfy_monthly,
    x="month",
    y="happiness_index",
    markers=True,
    title=f"Monthly Happiness Index — {year}"
)
fig.update_xaxes(dtick=1)
min_hi = dfy_monthly["happiness_index"].min() if not dfy_monthly.empty else None
low_cutoff = 221
mid_cutoff = 239  # adjust if you want a different upper bound
high_cutoff = 240
max_hi = dfy_monthly["happiness_index"].max() if not dfy_monthly.empty else None
margin = (
    max(10, 0.15 * (max_hi - min_hi))
    if (max_hi is not None and min_hi is not None)
    else 10
)
y_min = max(0, (min_hi - margin)) if min_hi is not None else 0
y_max = (max_hi + margin) if max_hi is not None else (high_cutoff + 10)

# Background bands for happiness index thresholds
band1_y0 = y_min
band1_y1 = min(low_cutoff, y_max)
if band1_y1 > band1_y0:
    fig.add_hrect(
        y0=band1_y0,
        y1=band1_y1,
        fillcolor="rgba(255,0,0,0.07)",
        line_width=0,
        layer="below",
    )

band2_y0 = max(low_cutoff, y_min)
band2_y1 = min(mid_cutoff, y_max)
if band2_y1 > band2_y0:
    fig.add_hrect(
        y0=band2_y0,
        y1=band2_y1,
        fillcolor="rgba(255,215,0,0.08)",
        line_width=0,
        layer="below",
    )

band3_y0 = max(high_cutoff, y_min)
band3_y1 = y_max
if band3_y1 > band3_y0:
    fig.add_hrect(
        y0=band3_y0,
        y1=band3_y1,
        fillcolor="rgba(0,128,0,0.07)",
        line_width=0,
        layer="below",
    )

fig.update_yaxes(title="happiness_index", range=[y_min, y_max])
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Emotion distribution (days)
emotion_counts = (
    dfy_all.groupby("emotion", as_index=False)
    .agg(days=("date", "count"), total=("score", "sum"))
)
emotion_order = [
    "Happy",
    "Productive",
    "Good",
    "Tired",
    "Lazy",
    "SAD",
    "Stress/Anxiety",
    "Angry/Annoyed",
    "Depressed",
    "Hopeless",
    "Suicidal",
]
emotion_counts["emotion"] = pd.Categorical(
    emotion_counts["emotion"], categories=emotion_order, ordered=True
)
emotion_counts = emotion_counts.sort_values("emotion")
emotion_color_map = (
    dfy_all[["emotion", "color_hex"]]
    .dropna(subset=["emotion", "color_hex"])
    .drop_duplicates(subset="emotion", keep="first")
    .set_index("emotion")["color_hex"]
    .to_dict()
)

c1, c2 = st.columns(2)

with c1:
    bar_data = emotion_counts.sort_values("days", ascending=False)
    fig2 = px.bar(
        bar_data,
        x="emotion",
        y="days",
        color="emotion",
        color_discrete_map=emotion_color_map or None,
        title="Days by Emotion",
    )
    fig2.update_xaxes(showticklabels=False, title=None)
    st.plotly_chart(fig2, use_container_width=True)

with c2:
    fig3 = px.pie(
        emotion_counts,
        names="emotion",
        values="days",
        color="emotion",
        color_discrete_map=emotion_color_map or None,
        category_orders={"emotion": emotion_order},
        title="Emotion Share (Days)",
    )
    st.plotly_chart(fig3, use_container_width=True)

with st.expander("Show raw data (year)"):
    st.dataframe(dfy_all.sort_values("date"), use_container_width=True)
