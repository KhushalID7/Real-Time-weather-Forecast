import os
import json
import requests
from dotenv import load_dotenv

# Load env
load_dotenv()

CACHE_PATH = os.path.join("data", "location_cache.json")


def _save_cache(lat, lon):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump({"latitude": lat, "longitude": lon}, f)


def _load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            data = json.load(f)
            return float(data["latitude"]), float(data["longitude"])
    return None


def get_system_location():
    """
    Best-effort system location:
    1) .env override (recommended for deployment)
    2) cached value (fast)
    3) IP-based lookup using multiple free providers
    """

    # 1) ENV override
    lat_env = os.getenv("LATITUDE")
    lon_env = os.getenv("LONGITUDE")
    if lat_env and lon_env:
        return float(lat_env), float(lon_env)

    # 2) Cache
    cached = _load_cache()
    if cached:
        return cached

    # 3) Multiple providers fallback
    providers = [
        ("ipwho.is", "https://ipwho.is/"),
        ("ip-api", "http://ip-api.com/json/"),
        ("ipinfo", "https://ipinfo.io/json"),
    ]

    last_error = None

    for name, url in providers:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()

            # ipwho.is format
            if name == "ipwho.is":
                if data.get("success") is False:
                    raise RuntimeError(data.get("message", "ipwho.is failed"))
                lat = float(data["latitude"])
                lon = float(data["longitude"])

            # ip-api format
            elif name == "ip-api":
                if data.get("status") != "success":
                    raise RuntimeError(data.get("message", "ip-api failed"))
                lat = float(data["lat"])
                lon = float(data["lon"])

            # ipinfo format
            elif name == "ipinfo":
                loc = data.get("loc", None)  # "lat,lon"
                if not loc:
                    raise RuntimeError("ipinfo missing loc")
                lat, lon = map(float, loc.split(","))

            _save_cache(lat, lon)
            print(f"📍 Location detected via {name}: lat={lat}, lon={lon}")
            return lat, lon

        except Exception as e:
            last_error = e
            print(f"⚠️ Location provider failed ({name}): {e}")

    raise RuntimeError(f"Could not fetch system location from any provider: {last_error}")


def fetch_current_weather(latitude=None, longitude=None):
    """
    Fetch latest weather data from Open-Meteo forecast API.
    Returns dict with required fields.
    """
    from datetime import datetime

    if latitude is None or longitude is None:
        latitude, longitude = get_system_location()

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "surface_pressure"
        ]),
        "timezone": "auto"
    }

    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    hourly = data["hourly"]
    last_index = len(hourly["time"]) - 1

    payload = {
        "timestamp": hourly["time"][last_index],
        "temperature": float(hourly["temperature_2m"][last_index]),
        "humidity": float(hourly["relative_humidity_2m"][last_index]),
        "wind_speed": float(hourly["wind_speed_10m"][last_index]),
        "pressure": float(hourly["surface_pressure"][last_index]),
        "latitude": latitude,
        "longitude": longitude,
        "fetched_at_utc": datetime.utcnow().isoformat()
    }

    return payload
