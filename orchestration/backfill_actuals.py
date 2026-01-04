import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta

# -------------------------------------------------
# Make project root importable
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PRED_PATH = "data/predictions/predictions.csv"

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

PARAMS_BASE = {
    "latitude": 23.2167,
    "longitude": 72.6833,
    "hourly": "temperature_2m",
    "timezone": "auto"
}


def backfill_actuals():
    if not os.path.exists(PRED_PATH):
        print("⚠️ No predictions file yet")
        return

    df = pd.read_csv(PRED_PATH, parse_dates=["timestamp"])

    missing = df[df["actual_temperature"].isna()]

    if missing.empty:
        print("✅ No missing actuals")
        return

    for idx, row in missing.iterrows():
        target_time = row["timestamp"] + timedelta(hours=1)

        params = PARAMS_BASE.copy()
        params["start_date"] = target_time.strftime("%Y-%m-%d")
        params["end_date"] = target_time.strftime("%Y-%m-%d")

        response = requests.get(OPEN_METEO_ARCHIVE, params=params)
        response.raise_for_status()

        hourly = response.json()["hourly"]
        times = hourly["time"]

        if target_time.strftime("%Y-%m-%dT%H:00") in times:
            i = times.index(target_time.strftime("%Y-%m-%dT%H:00"))
            df.loc[idx, "actual_temperature"] = hourly["temperature_2m"][i]

    df.to_csv(PRED_PATH, index=False)
    print("✅ Backfilled actual temperatures")


if __name__ == "__main__":
    backfill_actuals()
