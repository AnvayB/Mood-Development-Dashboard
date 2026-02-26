import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

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
    df["month_name"] = df["month"].map(lambda m: MONTH_NAMES[m-1])
    df["year_month"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str) + "-01"
    )
    return df

df = load_all()

st.title("Emotion Analysis")

# Define emotion order
EMOTION_ORDER = [
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
    "Horrible"
]

# Get available emotions and sort by custom order
all_emotions = df["emotion"].unique().tolist()
# Create ordered list, preserving order for emotions in EMOTION_ORDER, then adding any others
ordered_emotions = [e for e in EMOTION_ORDER if e in all_emotions]
remaining = [e for e in all_emotions if e not in EMOTION_ORDER]
ordered_emotions.extend(sorted(remaining))

# ----------------------------
# Section 1 — Emotion trend over time
# ----------------------------
# Create inline subheader with dropdown: [Emotion] over time
subheader_container = st.container()
with subheader_container:
    # TO ADJUST DROPDOWN WIDTH: Change the column ratios below (e.g., [0.28, 0.72] → [0.35, 0.65] for wider dropdown)
    header_col1, header_col2 = st.columns([0.28, 2])
    with header_col1:
        emotion = st.selectbox(
            "Emotion",
            ordered_emotions,
            index=ordered_emotions.index("Happy") if "Happy" in ordered_emotions else 0,
            label_visibility="collapsed",
            key="emotion_select"
        )
    with header_col2:
        st.markdown(f"<h4 style='margin-top: 0; padding-top: 12px; margin-bottom: 0;'>over time</h4>", unsafe_allow_html=True)

# Precompute total logged days per year-month (across all emotions) for % calculation
total_per_ym = (
    df.groupby("year_month", as_index=False)
      .agg(total_days=("date", "count"))
)

trend = (
    df[df["emotion"] == emotion]
    .groupby(["year", "month", "year_month"], as_index=False)
    .agg(days=("date", "count"))
    .sort_values("year_month")
)

trend = trend.merge(total_per_ym, on="year_month", how="left")
trend["pct_month"] = (trend["days"] / trend["total_days"] * 100).round(1)

fig = px.line(
    trend,
    x="year_month",
    y="pct_month",
    markers=True,
    title=f"{emotion} — % of days per month"
)

trend["roll3"] = trend["pct_month"].rolling(3, min_periods=1).mean()
fig.add_scatter(
    x=trend["year_month"],
    y=trend["roll3"],
    mode="lines",
    name="3-month avg",
    line=dict(dash="dash")
)

# Position the legend in the top right
fig.update_layout(
    height=420,
    xaxis_title="",
    yaxis_title="% of month",
    yaxis=dict(ticksuffix="%"),
    legend=dict(
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top"
    )
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ----------------------------
# Section 2 — Seasonality heatmap
# ----------------------------
st.subheader("Seasonality (emotion × month)")

heat = (
    df[df["emotion"] == emotion]
    .groupby(["year", "month"], as_index=False)
    .agg(days=("date", "count"))
)

pivot = (
    heat.pivot(index="year", columns="month", values="days")
        .reindex(columns=range(1,13))
        .astype(float)
)

pivot.columns = [MONTH_NAMES[m-1] for m in pivot.columns]

fig_hm = px.imshow(
    pivot,
    aspect="auto",
    title=f"{emotion} — days per month",
    color_continuous_scale="Blues_r",  # Reversed scale: darker = more frequent
)
fig_hm.update_layout(height=520, xaxis_title="", yaxis_title="")
st.plotly_chart(fig_hm, use_container_width=True)

st.divider()

# ----------------------------
# Section 3 — Total days per year
# ----------------------------
st.subheader("Total days per year")

yearly = (
    trend.groupby("year", as_index=False)
         .agg(total_days=("days", "sum"))
)

fig_yearly = px.bar(
    yearly,
    x="year",
    y="total_days",
    text="total_days",
    title=f"{emotion} — Total days per year",
)
fig_yearly.update_layout(
    height=360,
    xaxis_title="",
    yaxis_title="Days",
    xaxis=dict(dtick=1),
)
fig_yearly.update_traces(textposition="outside")
st.plotly_chart(fig_yearly, use_container_width=True)

st.divider()

# ----------------------------
# Section 4 — Drill-down
# ----------------------------
with st.expander("Drill-down by month"):
    c1, c2 = st.columns(2)
    with c1:
        yr = st.selectbox("Year", sorted(df["year"].unique()))
    with c2:
        mo = st.selectbox("Month", list(range(1,13)), format_func=lambda m: MONTH_NAMES[m-1])

    drill = df[
        (df["emotion"] == emotion) &
        (df["year"] == yr) &
        (df["month"] == mo)
    ].sort_values("date").copy()

    # Format date to remove timestamp (show only date)
    drill["date"] = drill["date"].dt.date

    st.dataframe(drill[["date","emotion","score","sheet","color_hex"]], use_container_width=True)
