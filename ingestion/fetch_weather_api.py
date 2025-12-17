import requests

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": 23.2167,
    "longitude": 72.6833,
    "start_date": "2024-09-01",
    "end_date": "2024-12-01",
    "hourly": ",".join([
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "surface_pressure"
    ]),
    "timezone": "auto"
}

response = requests.get(BASE_URL, params=params, timeout=30)
response.raise_for_status()

data = response.json()
hourly = data.get("hourly", {})

print("Available keys:", list(hourly.keys()))
print("Total hours:", len(hourly.get("time", [])))


print({
    "time": hourly["time"][0],
    "temperature": hourly["temperature_2m"][0],
    "humidity": hourly["relative_humidity_2m"][0],
    "wind_speed": hourly["wind_speed_10m"][0],
    "pressure": hourly["surface_pressure"][0],
})