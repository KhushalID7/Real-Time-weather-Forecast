import os
import sys
from datetime import datetime, timedelta

import streamlit as st
from streamlit_autorefresh import st_autorefresh

import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

# -------------------------------------------------
# Path setup
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from db.mongo_client import get_db
from orchestration.retrain_pipeline import retrain

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Weather ML Monitoring Dashboard",
    layout="wide"
)
st_autorefresh(interval=10_000, key="dashboard_refresh")

st.title("🌦️ Real-Time Weather ML System")


db = get_db()
predictions_col = db["predictions"]

st.sidebar.header("Controls")

time_window_hours = st.sidebar.selectbox(
    "Time window (hours)",
    [6, 12, 24, 48, 72],
    index=2
)

if st.sidebar.button("🔄 Retrain Model"):
    with st.spinner("Retraining in progress..."):
        retrain()
    st.sidebar.success("Retraining completed")

cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)

docs = list(predictions_col.find(
    {"created_at": {"$gte": cutoff}},
    {"_id": 0}
).sort("created_at", 1))

if not docs:
    st.warning("No prediction data available yet")
    st.stop()

df = pd.DataFrame(docs)


df["created_at_utc"] = pd.to_datetime(df["created_at"], utc=True)  # treat naive as UTC
df["created_at_ist"] = df["created_at_utc"].dt.tz_convert("Asia/Kolkata")

st.subheader("📊 System KPIs")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Predictions", len(df))

with col2:
    last_pred_time = df["created_at_ist"].max()
    st.metric("Last Prediction Time", last_pred_time.strftime("%Y-%m-%d %H:%M %Z"))

with col3:
    available_actuals = df["actual_temperature"].notna().sum()
    st.metric("Actuals Available", available_actuals)

# -------------------------------------------------
# Prediction vs Actual Plot
# -------------------------------------------------
st.subheader("📈 Prediction vs Actual Temperature")

df_plot = df.dropna(subset=["actual_temperature"]).copy()

if df_plot.empty:
    st.info("Actual temperatures not yet available")
else:
    fig = px.line(
        df_plot,
        x="created_at_ist",
        y=["prediction", "actual_temperature"],
        labels={"value": "Temperature (°C)", "created_at_ist": "Time (IST)"},
        title="Predicted vs Actual Temperature (IST)"
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# Rolling MAE
# -------------------------------------------------
st.subheader("📉 Rolling MAE")

if len(df_plot) >= 5:
    df_plot["abs_error"] = (df_plot["prediction"] - df_plot["actual_temperature"]).abs()
    df_plot["rolling_mae"] = df_plot["abs_error"].rolling(window=5).mean()

    fig_mae = px.line(
        df_plot,
        x="created_at_ist",
        y="rolling_mae",
        labels={"rolling_mae": "MAE", "created_at_ist": "Time (IST)"},
        title="Rolling MAE (window=5, IST)"
    )
    st.plotly_chart(fig_mae, use_container_width=True)
else:
    st.info("Not enough data for MAE computation")

# -------------------------------------------------
# Raw Data (Optional)
# -------------------------------------------------
with st.expander("🗂️ View Raw Prediction Data"):
    st.dataframe(df.sort_values("created_at", ascending=False))
