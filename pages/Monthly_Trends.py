import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Widen content on this page
st.markdown(
    """
    <style>
    .block-container {
        max-width: 75vw !important;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

@st.cache_data
def load_monthly():
    df = pd.read_csv("data/mood_monthly_hi.csv")
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["happiness_index"] = pd.to_numeric(df["happiness_index"], errors="coerce").round(0).astype("Int64")
    df["month_name"] = df["month"].map(lambda m: MONTH_NAMES[m-1])
    df["year_month"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str) + "-01")
    return df.dropna(subset=["happiness_index"]).copy()

def add_hi_bands(fig, y_min, y_max):
    """
    Adds subtle background bands (red -> yellow -> green).
    Keeps the look similar to your Overview chart.
    """
    # Clamp if range is tight
    span = max(1, y_max - y_min)
    a = y_min + 0.33 * span
    b = y_min + 0.66 * span

    fig.add_hrect(y0=y_min, y1=a, fillcolor="rgba(255,0,0,0.08)", line_width=0)
    fig.add_hrect(y0=a, y1=b, fillcolor="rgba(255,255,0,0.07)", line_width=0)
    fig.add_hrect(y0=b, y1=y_max, fillcolor="rgba(0,255,0,0.08)", line_width=0)
    return fig

st.title("Monthly Trends")

dfm = load_monthly()
years = sorted(dfm["year"].unique().tolist())
if not years:
    st.error("No monthly data found in data/mood_monthly_hi.csv")
    st.stop()

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.subheader("Filters")
year_min, year_max = st.sidebar.slider(
    "Year range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

mode = st.sidebar.radio(
    "View",
    ["Trend over time", "Compare years", "Heatmap"],
    index=0
)

show_rolling = st.sidebar.checkbox("Show 3-month rolling average", value=True)

df = dfm[(dfm["year"] >= year_min) & (dfm["year"] <= year_max)].sort_values(["year","month"]).copy()
df_hi = df.dropna(subset=["happiness_index"]).copy()
if df_hi.empty:
    st.warning("No happiness index data available for the selected range.")
    st.stop()

# Helpful bounds for consistent charts
y_min = float(df_hi["happiness_index"].min())
y_max = float(df_hi["happiness_index"].max())

# -----------------------------
# 1) Trend over time (hero chart)
# -----------------------------
if mode == "Trend over time":
    st.subheader("Happiness Index over time")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_hi["year_month"],
        y=df_hi["happiness_index"],
        mode="lines+markers",
        name="HI",
        hovertemplate="%{x|%b %Y}<br>HI: %{y}<extra></extra>"
    ))

    if show_rolling:
        df_roll = df_hi.copy()
        df_roll["hi_roll3"] = df_roll["happiness_index"].astype(float).rolling(3, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=df_roll["year_month"],
            y=df_roll["hi_roll3"],
            mode="lines",
            name="Rolling (3-mo)",
            line=dict(dash="dash"),
            hovertemplate="%{x|%b %Y}<br>3-mo avg: %{y:.1f}<extra></extra>"
        ))

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="",
        yaxis_title="Happiness Index",
        legend_title="",
    )
    fig = add_hi_bands(fig, y_min, y_max)
    st.plotly_chart(fig, use_container_width=True)

    # Quick “best/worst” summary for the selected range
    st.divider()
    c1, c2, c3 = st.columns(3)

    best_row = df_hi.loc[df_hi["happiness_index"].idxmax()]
    worst_row = df_hi.loc[df_hi["happiness_index"].idxmin()]
    avg_hi = float(df_hi["happiness_index"].mean())

    c1.metric("Avg HI (selected range)", round(avg_hi, 1))
    c2.metric("Best month", f"{best_row['month_name']} {best_row['year']}", int(best_row["happiness_index"]))
    c3.metric("Worst month", f"{worst_row['month_name']} {worst_row['year']}", int(worst_row["happiness_index"]))

    with st.expander("Show table (selected range)"):
        out = df_hi[["year","month","month_name","happiness_index","source_sheet"]].copy()
        out = out.sort_values(["year","month"]).reset_index(drop=True)
        st.dataframe(out, use_container_width=True)

# -----------------------------
# 2) Compare years (same-month YoY)
# -----------------------------
elif mode == "Compare years":
    st.subheader("Compare years (same month across years)")

    month_sel = st.selectbox(
        "Month",
        list(range(1, 13)),
        index=0,
        format_func=lambda m: MONTH_NAMES[m-1]
    )

    dfx = df_hi[df_hi["month"] == month_sel].sort_values("year").copy()

    fig = px.bar(
        dfx,
        x="year",
        y="happiness_index",
        text="happiness_index",
        title=f"HI for {MONTH_NAMES[month_sel-1]} across years",
    )
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="", yaxis_title="Happiness Index")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 3) Heatmap (pattern finder)
# -----------------------------
else:
    st.subheader("Heatmap (Year × Month)")

    pivot = (
        df.pivot_table(index="year", columns="month", values="happiness_index", aggfunc="mean")
          .reindex(columns=list(range(1, 13)))
    )

    # ✅ Fix: Plotly can't serialize pd.NA (NAType). Convert to float + np.nan.
    pivot = pivot.astype(float).to_numpy()  # values become float with np.nan

    # Build labeled dataframe for px.imshow
    heat_df = pd.DataFrame(
        pivot,
        index=sorted(df["year"].unique()),
        columns=[MONTH_NAMES[m-1] for m in range(1, 13)]
    )

    fig = px.imshow(
        heat_df,
        aspect="auto",
        title="Monthly Happiness Index Heatmap",
    )
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="",
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Tip: this view is great for spotting seasonal patterns or recurring low/high months.")
