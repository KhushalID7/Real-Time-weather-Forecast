import json
import time
import requests
from kafka import KafkaProducer
from datetime import datetime, timezone, timedelta

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

TOPIC = "weather_raw"

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# ----------------------------
# Open-Meteo API Config
# ----------------------------
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 23.2167,
    "longitude": 72.6833,
    "hourly": ",".join([
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "surface_pressure"
    ]),
    "timezone": "Asia/Kolkata",
    "forecast_days": 1
}

print("🚀 Weather producer started (IST)")

while True:
    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()

    hourly = response.json()["hourly"]

    # Get current IST time
    now_ist = datetime.now(IST)
    
    # Parse all times and localize to IST
    times = []
    for t in hourly["time"]:
        dt = datetime.fromisoformat(t)
        # If naive, localize to IST
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        times.append(dt)
    
    # Find the latest timestamp that's not in the future
    recent_idx = None
    for idx, t in enumerate(times):
        if t <= now_ist:
            recent_idx = idx
        else:
            break
    
    if recent_idx is None:
        print("⚠️ No current data available, skipping...")
        time.sleep(30)
        continue
    
    i = recent_idx

    message = {
        "timestamp": hourly["time"][i],
        "temperature": hourly["temperature_2m"][i],
        "humidity": hourly["relative_humidity_2m"][i],
        "wind_speed": hourly["wind_speed_10m"][i],
        "pressure": hourly["surface_pressure"][i]
    }

    producer.send(TOPIC, message)
    producer.flush()

    print(f"📤 Sent weather message (IST): {message['timestamp']} | Temp: {message['temperature']}°C")

    time.sleep(30)
