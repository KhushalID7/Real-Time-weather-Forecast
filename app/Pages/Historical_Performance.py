import os, sys
from datetime import datetime, timedelta, timezone
import streamlit as st
import pandas as pd
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
# IST Timezone
# -------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Historical Performance | Weather ML",
    layout="wide"
)

st.title("📊 Historical Performance — Evaluated Predictions")

# -------------------------------------------------
# MongoDB
# -------------------------------------------------
db = get_db()
predictions = db["predictions"]

# -------------------------------------------------
# Fetch evaluated predictions (7 days default)
# -------------------------------------------------
now_ist = datetime.now(IST)
cutoff = now_ist - timedelta(days=7)
cutoff_iso = cutoff.isoformat()

docs = list(predictions.find(
    {
        "actual_temperature": {"$ne": None},
        "created_at": {"$gte": cutoff_iso}
    },
    {"_id": 0}
).sort("created_at", -1))

if not docs:
    st.warning(f"❌ No evaluated predictions in the last 7 days.")
    st.info("Predictions need ~1 hour to get actual temperatures via backfill.")
    st.stop()

df = pd.DataFrame(docs)

# -------------------------------------------------
# Compute metrics
# -------------------------------------------------
df["error"] = abs(df["prediction"] - df["actual_temperature"])
df["percent_error"] = (df["error"] / df["actual_temperature"].abs()) * 100

mae = df["error"].mean()
rmse = (df["error"] ** 2).mean() ** 0.5
mape = df["percent_error"].mean()

# -------------------------------------------------
# KPIs
# -------------------------------------------------
st.subheader("📈 Evaluation Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Evaluated", len(df))

with col2:
    st.metric("MAE (°C)", f"{mae:.3f}")

with col3:
    st.metric("RMSE (°C)", f"{rmse:.3f}")

with col4:
    st.metric("MAPE (%)", f"{mape:.2f}%")

with col5:
    st.metric("Time Range", "7d")

# -------------------------------------------------
# Charts
# -------------------------------------------------
st.subheader("📉 Performance Analysis")

st.subheader("Prediction vs Actual")
chart_df = df.sort_values("timestamp")[["prediction", "actual_temperature"]].rename(
    columns={"prediction": "Predicted", "actual_temperature": "Actual"}
)
st.line_chart(chart_df, height=400)

# -------------------------------------------------
# Detailed Table
# -------------------------------------------------
st.subheader("🔬 Detailed Predictions")

display_df = df.sort_values("timestamp", ascending=False).copy()
display_df["prediction"] = display_df["prediction"].apply(lambda x: f"{x:.2f}°C")
display_df["actual_temperature"] = display_df["actual_temperature"].apply(lambda x: f"{x:.2f}°C")
display_df["error"] = display_df["error"].apply(lambda x: f"{x:.3f}°C")
display_df["created_at"] = display_df["created_at"].apply(
    lambda x: x[:19] if isinstance(x, str) else str(x)[:19]
)

st.dataframe(
    display_df[["timestamp", "prediction", "actual_temperature", "error", "model_name", "created_at"]],
    use_container_width=True,
    height=500
)

# -------------------------------------------------
# Summary Stats
# -------------------------------------------------
st.subheader("📊 Summary Statistics")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.metric("Min Error", f"{df['error'].min():.3f}°C")
    st.metric("Max Error", f"{df['error'].max():.3f}°C")

with summary_col2:
    st.metric("Std Dev Error", f"{df['error'].std():.3f}°C")
    st.metric("Median Error", f"{df['error'].median():.3f}°C")

with summary_col3:
    best_pred = df.loc[df['error'].idxmin()]
    worst_pred = df.loc[df['error'].idxmax()]
    st.metric("Best Prediction", f"{best_pred['error']:.3f}°C @ {best_pred['timestamp']}")
    st.metric("Worst Prediction", f"{worst_pred['error']:.3f}°C @ {worst_pred['timestamp']}")
