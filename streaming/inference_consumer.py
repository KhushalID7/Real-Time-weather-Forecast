import os, sys
# -------------------------------------------------
# Make project root importable when running directly
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime, timezone, timedelta
import json
import pandas as pd
import numpy as np
from kafka import KafkaConsumer
from collections import deque

from db.mongo_client import get_db
from model.inference import ModelInferenceEngine

# Configuration
# =========================================================
TOPIC = os.getenv("KAFKA_TOPIC", "weather_raw")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "6"))
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "weather-inference-group")

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# =========================================================
# Kafka Consumer
# =========================================================
from kafka.errors import NoBrokersAvailable
import time

MAX_RETRIES = 12
consumer = None
for i in range(MAX_RETRIES):
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id=CONSUMER_GROUP,
            auto_offset_reset="latest"
        )
        break
    except NoBrokersAvailable:
        print(f"⏳ Waiting for Kafka to be ready... ({i+1}/{MAX_RETRIES})")
        time.sleep(5)

if consumer is None:
    raise RuntimeError("❌ Could not connect to Kafka after multiple retries.")

# =========================================================
# Sliding Window Buffer
# =========================================================
buffer = deque(maxlen=WINDOW_SIZE + 1)  # current + 6 previous

# =========================================================
# Load Best Model
# =========================================================
engine = ModelInferenceEngine()
print("🚀 Inference consumer started (IST)")

# =========================================================
# MongoDB
# =========================================================
db = get_db()
predictions_col = db["predictions"]

# Feature Builder (must match training exactly)
# =========================================================
META_PATH = os.path.join(PROJECT_ROOT, "model", "artifacts", "best_model_meta.json")
if not os.path.exists(META_PATH):
    # Fallback for different directory structures in Docker
    META_PATH = "/app/model/artifacts/best_model_meta.json"

with open(META_PATH, "r") as f:
    META = json.load(f)
FEATURE_COLUMNS = META.get("feature_columns")

def build_features(prev_window):
    row = {}
    for i, record in enumerate(reversed(prev_window), start=1):
        row[f"temp_t-{i}"] = record["temperature"]
        row[f"humidity_t-{i}"] = record["humidity"]
        row[f"wind_speed_t-{i}"] = record["wind_speed"]
        row[f"pressure_t-{i}"] = record["pressure"]

    ts = pd.to_datetime(prev_window[-1]["timestamp"])
    row["hour"] = ts.hour
    row["day_of_week"] = ts.dayofweek
    row["month"] = ts.month
    row["day_of_year"] = ts.dayofyear

    # cyclic features
    row["sin_hour"] = np.sin(2 * np.pi * row["hour"] / 24)
    row["cos_hour"] = np.cos(2 * np.pi * row["hour"] / 24)
    row["sin_doy"] = np.sin(2 * np.pi * row["day_of_year"] / 365.25)
    row["cos_doy"] = np.cos(2 * np.pi * row["day_of_year"] / 365.25)

    # slope / rolling features
    row["temp_diff_1"] = row["temp_t-1"] - row["temp_t-2"]
    row["temp_diff_2"] = row["temp_t-2"] - row["temp_t-3"]
    row["temp_rm_3"] = (row["temp_t-1"] + row["temp_t-2"] + row["temp_t-3"]) / 3
    row["temp_rm_6"] = (
        row["temp_t-1"] + row["temp_t-2"] + row["temp_t-3"] +
        row["temp_t-4"] + row["temp_t-5"] + row["temp_t-6"]
    ) / 6

    df = pd.DataFrame([row])
    if FEATURE_COLUMNS:
        df = df.reindex(columns=FEATURE_COLUMNS)
    return df

# =========================================================
# Consume Messages & Run Inference
# =========================================================
for message in consumer:
    data = message.value
    buffer.append(data)
    print("📥 Received:", data)

    if len(buffer) < WINDOW_SIZE + 1:
        print(f"⏳ Waiting for {WINDOW_SIZE + 1 - len(buffer)} more messages")
        continue

    prev_window = list(buffer)[:-1]
    X = build_features(prev_window)
    prediction = float(engine.predict(X)[0])

    print(
        f"📈 Prediction | time={data['timestamp']} "
        f"| temp+1h={prediction:.2f}°C "
        f"| model={engine.model_name}"
    )

    # Get current time in IST and format as ISO string
    now_ist = datetime.now(IST)
    created_at_ist = now_ist.isoformat()

    doc = {
        "timestamp": data["timestamp"],
        "prediction": prediction,
        "actual_temperature": None,
        "model_name": engine.model_name,
        "created_at": created_at_ist
    }

    try:
        result = predictions_col.insert_one(doc)
        print("✅ Mongo insert OK | _id =", result.inserted_id)
        print(f"   🕐 Stored created_at (IST): {created_at_ist}")
    except Exception as e:
        print("❌ Mongo insert FAILED:", e)
