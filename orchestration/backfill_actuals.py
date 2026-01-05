import os, sys
import requests
from datetime import datetime, timedelta

# -------------------------------------------------
# Make project root importable
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.mongo_client import get_db

# -------------------------------------------------
# Open-Meteo archive API
# -------------------------------------------------
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

PARAMS_BASE = {
    "latitude": 23.2167,
    "longitude": 72.6833,
    "hourly": "temperature_2m",
    "timezone": "auto"
}


def backfill_actuals():
    db = get_db()
    predictions = db["predictions"]

    # -------------------------------------------------
    # Find predictions missing actuals
    # -------------------------------------------------
    missing_docs = list(predictions.find({
        "actual_temperature": None
    }))

    if not missing_docs:
        print("✅ No missing actuals")
        return

    print(f"🔄 Backfilling {len(missing_docs)} predictions")

    now_utc = datetime.utcnow()
    
    for doc in missing_docs:
        pred_time = datetime.fromisoformat(doc["timestamp"])
        target_time = pred_time + timedelta(hours=1)
    
        # 🚨 Skip future actuals
        if target_time > now_utc:
            print(f"⏭️ Skipping future target: {target_time}")
            continue
        
        params = PARAMS_BASE.copy()
        params["start_date"] = target_time.strftime("%Y-%m-%d")
        params["end_date"] = target_time.strftime("%Y-%m-%d")
    
        response = requests.get(OPEN_METEO_ARCHIVE, params=params, timeout=10)
    
        if response.status_code != 200:
            print(f"⚠️ Open-Meteo returned {response.status_code} for {target_time}")
            continue
        
        hourly = response.json().get("hourly", {})
        times = hourly.get("time", [])
    
        target_str = target_time.strftime("%Y-%m-%dT%H:00")
    
        if target_str in times:
            i = times.index(target_str)
            actual_temp = hourly["temperature_2m"][i]
    
            predictions.update_one(
                {"_id": doc["_id"]},
                {"$set": {"actual_temperature": float(actual_temp)}}
            )
    
            print(f"✅ Backfilled {str(doc['_id'])[-6:]} → {actual_temp}°C")


    print("🎉 Backfill complete")


def _short_id(obj_id):
    return str(obj_id)[-6:]


if __name__ == "__main__":
    backfill_actuals()
