import os, sys
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

# -------------------------------------------------
# Path & env
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from db.mongo_client import get_db

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Live Monitoring | Weather ML",
    layout="wide"
)

st_autorefresh(interval=10_000, key="live_refresh")

st.title("🟢 Live Monitoring — Real-Time Forecasting")

# -------------------------------------------------
# MongoDB
# -------------------------------------------------
db = get_db()
predictions = db["predictions"]

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.header("Live Controls")

window_hours = st.sidebar.selectbox(
    "View window (hours)",
    [6, 12, 24, 48],
    index=2
)

cutoff = datetime.utcnow() - timedelta(hours=window_hours)

docs = list(predictions.find(
    {"created_at": {"$gte": cutoff}},
    {"_id": 0}
).sort("created_at", 1))

if not docs:
    st.warning("No predictions generated yet.")
    st.stop()

df = pd.DataFrame(docs)

# -------------------------------------------------
# KPIs
# -------------------------------------------------
st.subheader("📊 System Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Predictions (window)", len(df))

with col2:
    st.metric(
        "Last Prediction",
        df["created_at"].max().strftime("%Y-%m-%d %H:%M UTC")
    )

with col3:
    actuals = df["actual_temperature"].notna().sum()
    st.metric("Actuals Available", actuals)

# -------------------------------------------------
# Status banner
# -------------------------------------------------
if actuals == 0:
    st.info(
        "⏳ Forecasts are being generated. "
        "Evaluation metrics will appear once real temperatures become available."
    )
else:
    st.success("✅ Some predictions have been evaluated. See Historical Performance page.")

# -------------------------------------------------
# Raw recent predictions
# -------------------------------------------------
st.subheader("🕒 Recent Predictions (Live)")

st.dataframe(
    df.sort_values("created_at", ascending=False).head(20),
    use_container_width=True
)
