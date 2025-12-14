import streamlit as st

st.set_page_config(page_title="Mood Dashboard", layout="wide")

st.title("Mood Dashboard")
st.write("Explore trends across years, monthly HI, and emotion breakdowns using the sidebar pages.")
st.info("Data is loaded from exported CSVs. Later we can switch this to live Google Sheets refresh.")
