import os
import streamlit as st

st.set_page_config(
    page_title="Risk, Fraud and Regulatory Intelligence Copilot",
    page_icon=":material/shield:",
    layout="wide",
)

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))
st.session_state["conn"] = conn

ACCENT = "#00D4AA"
ACCENT2 = "#6C63FF"
ACCENT3 = "#FF6B6B"
ACCENT4 = "#FFB347"
ACCENT5 = "#4FC3F7"
st.session_state["colors"] = {
    "accent": ACCENT,
    "purple": ACCENT2,
    "red": ACCENT3,
    "orange": ACCENT4,
    "blue": ACCENT5,
}

page = st.navigation(
    {
        "Risk, Fraud and Regulatory Intelligence Copilot": [
            st.Page("app_pages/risk_page.py", title="Risk Intelligence", icon=":material/warning:"),
            st.Page("app_pages/fraud_page.py", title="Fraud Intelligence", icon=":material/gpp_bad:"),
            st.Page("app_pages/compliance_page.py", title="Regulatory Intelligence", icon=":material/verified_user:"),
            st.Page("app_pages/alerts_page.py", title="Alerts & Monitoring", icon=":material/notifications_active:"),
            st.Page("app_pages/investigations_page.py", title="Investigations", icon=":material/search:"),
            st.Page("app_pages/reports_page.py", title="Reports & Insights", icon=":material/insights:"),
            st.Page("app_pages/documents_page.py", title="Document Analysis", icon=":material/description:"),
        ],
    },
    position="sidebar",
)

page.run()
