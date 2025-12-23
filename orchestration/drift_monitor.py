import os
import sys
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sklearn.metrics import mean_absolute_error

# -------------------------------------------------
# Make project root importable
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from db.mongo_client import get_db
from orchestration.retrain_pipeline import retrain


# -------------------------------------------------
# Configuration
# -------------------------------------------------
CHECK_INTERVAL_MINUTES = 60          # how often to check drift
ROLLING_WINDOW_HOURS = 24            # window for MAE
DRIFT_MULTIPLIER = 1.5               # sensitivity


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def load_baseline_mae():
    path = os.path.join(PROJECT_ROOT, "model", "artifacts", "best_model.json")
    with open(path, "r") as f:
        meta = json.load(f)
    return meta["test_mae"]


# -------------------------------------------------
# Drift Check Logic
# -------------------------------------------------
def check_drift():
    db = get_db()
    predictions_col = db["predictions"]

    cutoff = datetime.utcnow() - timedelta(hours=ROLLING_WINDOW_HOURS)

    docs = list(predictions_col.find({
        "actual_temperature": {"$ne": None},
        "created_at": {"$gte": cutoff}
    }))

    if len(docs) < 10:
        print("⏳ Not enough data to evaluate drift")
        return

    y_true = [d["actual_temperature"] for d in docs]
    y_pred = [d["prediction"] for d in docs]

    rolling_mae = mean_absolute_error(y_true, y_pred)
    baseline_mae = load_baseline_mae()

    print(f"📊 Rolling MAE ({ROLLING_WINDOW_HOURS}h): {rolling_mae:.3f}")
    print(f"📏 Baseline MAE: {baseline_mae:.3f}")

    if rolling_mae > baseline_mae * DRIFT_MULTIPLIER:
        print("🚨 Drift detected — triggering retraining")
        retrain()
    else:
        print("✅ No drift detected")


# -------------------------------------------------
# Continuous Monitor
# -------------------------------------------------
def run_drift_monitor():
    print("🛰️ Drift monitor started")
    print(
        f"🔁 Checking every {CHECK_INTERVAL_MINUTES} min | "
        f"Window={ROLLING_WINDOW_HOURS}h | "
        f"Threshold={DRIFT_MULTIPLIER}×"
    )

    while True:
        try:
            check_drift()
        except Exception as e:
            print("❌ Drift monitor error:", e)

        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    run_drift_monitor()
