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


# =========================================================
# Configuration
# =========================================================
TOPIC = "weather_raw"
BOOTSTRAP_SERVERS = "localhost:9092"
WINDOW_SIZE = 6
CONSUMER_GROUP = "weather-inference-group"


# =========================================================
# Kafka Consumer
# =========================================================
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    group_id=CONSUMER_GROUP,
    auto_offset_reset="latest"   # real-time inference
)


# =========================================================
# Sliding Window Buffer
# =========================================================
buffer = deque(maxlen=WINDOW_SIZE)


# =========================================================
# Load Best Model Automatically
# =========================================================
engine = ModelInferenceEngine()

print("🚀 Inference consumer started")


# =========================================================
# Feature Builder (MUST MATCH TRAINING)
# =========================================================
def build_features(window):
    """
    Build feature row exactly as used during training
    (NO raw temperature/humidity/pressure columns)
    """
    row = {}

    # Lag features: t-1 → t-6
    for i, record in enumerate(reversed(window), start=1):
        row[f"temp_t-{i}"] = record["temperature"]
        row[f"humidity_t-{i}"] = record["humidity"]
        row[f"wind_speed_t-{i}"] = record["wind_speed"]
        row[f"pressure_t-{i}"] = record["pressure"]

    # Time features
    ts = pd.to_datetime(window[-1]["timestamp"])
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

    if len(buffer) < WINDOW_SIZE:
        print(f"⏳ Waiting for {WINDOW_SIZE - len(buffer)} more messages")
        continue

    X = build_features(buffer)

    prediction = engine.predict(X)[0]

    print(
        f"📈 Prediction | time={data['timestamp']} "
        f"| temp+1h={prediction:.2f}°C "
        f"| model={engine.model_name}"
    )

