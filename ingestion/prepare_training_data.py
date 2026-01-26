import os, sys
import pandas as pd
from datetime import timezone, timedelta

# -------------------------------------------------
# Make project root importable
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from features.feature_engineering import create_supervised_dataset

RAW_PATH = "data/processed/weather_5y_raw.csv"
SUPERVISED_PATH = "data/processed/supervised_weather.csv"

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))


def prepare_supervised_from_5y_raw(n_lags=6):
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"❌ Missing raw file: {RAW_PATH}")

    # parse timestamps
    df_raw = pd.read_csv(RAW_PATH, parse_dates=["timestamp"])

    # ensure timezone-aware in IST
    if df_raw["timestamp"].dt.tz is None:
        df_raw["timestamp"] = df_raw["timestamp"].dt.tz_localize("Asia/Kolkata")
    else:
        df_raw["timestamp"] = df_raw["timestamp"].dt.tz_convert("Asia/Kolkata")

    # Validate columns
    required_cols = ["timestamp", "temperature", "humidity", "wind_speed", "pressure"]
    for c in required_cols:
        if c not in df_raw.columns:
            raise ValueError(f"❌ Column missing in raw file: {c}")

    # Rename to match feature_engineering expectations
    df_raw = df_raw.rename(columns={
        "timestamp": "time",
        "temperature": "temperature_2m",
        "humidity": "relative_humidity_2m",
        "wind_speed": "wind_speed_10m",
        "pressure": "surface_pressure",
    })

    # Create hourly_data dict (strings for time)
    hourly_data = {
        "time": df_raw["time"].dt.strftime("%Y-%m-%dT%H:%M").tolist(),
        "temperature_2m": df_raw["temperature_2m"].tolist(),
        "relative_humidity_2m": df_raw["relative_humidity_2m"].tolist(),
        "wind_speed_10m": df_raw["wind_speed_10m"].tolist(),
        "surface_pressure": df_raw["surface_pressure"].tolist(),
    }

    # Create supervised dataset
    df_supervised = create_supervised_dataset(hourly_data, n_lags=n_lags)

    os.makedirs(os.path.dirname(SUPERVISED_PATH), exist_ok=True)
    df_supervised.to_csv(SUPERVISED_PATH, index=False)

    print("✅ Supervised dataset created (IST)")
    print("📄 Saved to:", SUPERVISED_PATH)
    print("📊 Shape:", df_supervised.shape)
    print("🧾 Columns:", list(df_supervised.columns))


if __name__ == "__main__":
    prepare_supervised_from_5y_raw(n_lags=6)
