import json
import time
import requests
from kafka import KafkaProducer


producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

TOPIC = "weather_raw"

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
    "timezone": "auto"
}

print("🚀 Weather producer started")

while True:
    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()

    hourly = response.json()["hourly"]

    # latest available hour
    i = -1

    message = {
        "timestamp": hourly["time"][i],
        "temperature": hourly["temperature_2m"][i],
        "humidity": hourly["relative_humidity_2m"][i],
        "wind_speed": hourly["wind_speed_10m"][i],
        "pressure": hourly["surface_pressure"][i]
    }

    producer.send(TOPIC, message)
    producer.flush()

    print("📤 Sent weather message:", message)

    # for testing you can reduce this to 30–60 seconds
    time.sleep(60)
