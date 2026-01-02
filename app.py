import streamlit as st

st.set_page_config(page_title="Mood Dashboard", layout="wide")

# Disable the "app" link in sidebar navigation
st.markdown(
    """
    <style>
    /* Disable the first navigation link (app.py) in the sidebar */
    ul[data-testid="stSidebarNav"] li:first-child a {
        pointer-events: none !important;
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Redirect to Overview page
st.switch_page("pages/0_Overview.py")
