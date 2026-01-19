import os, sys
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# -------------------------------------------------
# Path & env
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from db.mongo_client import get_db

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Historical Performance | Weather ML",
    layout="wide"
)

st.title("📉 Historical Performance — Evaluated Predictions")

# -------------------------------------------------
# MongoDB
# -------------------------------------------------
db = get_db()
predictions = db["predictions"]

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.header("Filters")

window_days = st.sidebar.selectbox(
    "Time range",
    [1, 3, 7, 14, 30, "All"],
    index=3
)

query = {"actual_temperature": {"$ne": None}}

if window_days != "All":
    cutoff = datetime.utcnow() - timedelta(days=int(window_days))
    query["created_at"] = {"$gte": cutoff}

docs = list(predictions.find(query, {"_id": 0}).sort("created_at", 1))

if not docs:
    st.warning("No evaluated predictions available yet.")
    st.stop()

df = pd.DataFrame(docs)

# -------------------------------------------------
# Prediction vs Actual
# -------------------------------------------------
st.subheader("📈 Prediction vs Actual Temperature")

fig = px.line(
    df,
    x="created_at",
    y=["prediction", "actual_temperature"],
    labels={"value": "Temperature (°C)", "created_at": "Time"},
)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# Rolling MAE
# -------------------------------------------------
st.subheader("📊 Rolling MAE")

df["abs_error"] = (df["prediction"] - df["actual_temperature"]).abs()
df["rolling_mae"] = df["abs_error"].rolling(window=5).mean()

fig_mae = px.line(
    df,
    x="created_at",
    y="rolling_mae",
    labels={"rolling_mae": "MAE", "created_at": "Time"},
)
st.plotly_chart(fig_mae, use_container_width=True)

# -------------------------------------------------
# Data table
# -------------------------------------------------
with st.expander("📄 View evaluated data"):
    st.dataframe(
        df.sort_values("created_at", ascending=False),
        use_container_width=True
    )
