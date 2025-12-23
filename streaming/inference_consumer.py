import os, sys
# Make project root importable when running this file directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import pandas as pd
from kafka import KafkaConsumer
from collections import deque

from model.inference import ModelInferenceEngine

os.makedirs("data/predictions", exist_ok=True)

# =========================================================
# Configuration
# =========================================================
TOPIC = "weather_raw"
BOOTSTRAP_SERVERS = "localhost:9092"
WINDOW_SIZE = 6              # number of lags used in training
CONSUMER_GROUP = "weather-inference-group"


# =========================================================
# Kafka Consumer
# =========================================================
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    group_id=CONSUMER_GROUP,
    auto_offset_reset="latest"
)


# =========================================================
# Sliding Window Buffer
# =========================================================
buffer = deque(maxlen=WINDOW_SIZE + 1)   # include current + 6 previous


# =========================================================
# Load Best Model Automatically
# =========================================================
engine = ModelInferenceEngine()
print("🚀 Inference consumer started")


# =========================================================
# Feature Builder (must match training)
# =========================================================
def build_features(prev_window):
    """
    Build feature row from the previous 6 records (t-1..t-6).
    """
    row = {}
    for i, record in enumerate(reversed(prev_window), start=1):
        row[f"temp_t-{i}"] = record["temperature"]
        row[f"humidity_t-{i}"] = record["humidity"]
        row[f"wind_speed_t-{i}"] = record["wind_speed"]
        row[f"pressure_t-{i}"] = record["pressure"]

    ts = pd.to_datetime(prev_window[-1]["timestamp"])
    row["hour"] = ts.hour
    row["day_of_week"] = ts.dayofweek
    return pd.DataFrame([row])


# =========================================================
# Consume Messages & Run Inference
# =========================================================
for message in consumer:
    data = message.value
    buffer.append(data)
    print("📥 Received:", data)

    # need 6 previous + current
    if len(buffer) < WINDOW_SIZE + 1:
        print(f"⏳ Waiting for {WINDOW_SIZE + 1 - len(buffer)} more messages")
        continue

    prev_window = list(buffer)[:-1]        # exclude current reading
    X = build_features(prev_window)
    prediction = float(engine.predict(X)[0])

    print(f"📈 Prediction | time={data['timestamp']} | temp+1h={prediction:.2f}°C | model={engine.model_name}")

    # Log prediction after it is computed
    log_row = {
        "timestamp": data["timestamp"],
        "prediction": prediction,
        "actual_temperature": None
    }
    log_path = "data/predictions/predictions.csv"
    df_log = pd.DataFrame([log_row])
    if not os.path.exists(log_path):
        df_log.to_csv(log_path, index=False)
    else:
        df_log.to_csv(log_path, mode="a", header=False, index=False)

