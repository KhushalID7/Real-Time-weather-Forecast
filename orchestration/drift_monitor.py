import os
import sys
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from sklearn.metrics import mean_absolute_error

# -------------------------------------------------
# Make project root importable
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from orchestration.retrain_pipeline import retrain


# -------------------------------------------------
# Configuration
# -------------------------------------------------
PREDICTION_LOG = "data/predictions/predictions.csv"
CHECK_INTERVAL_MINUTES = 60
ROLLING_WINDOW_HOURS = 24
DRIFT_MULTIPLIER = 1.5


def load_baseline_mae():
    with open("model/artifacts/best_model.json", "r") as f:
        metadata = json.load(f)
    return metadata["test_mae"]


def check_drift():
    if not os.path.exists(PREDICTION_LOG):
        print("⚠️ No prediction data available yet")
        return

    df = pd.read_csv(PREDICTION_LOG, parse_dates=["timestamp"])

    cutoff_time = datetime.now() - timedelta(hours=ROLLING_WINDOW_HOURS)
    recent = df[df["timestamp"] >= cutoff_time]

    if len(recent) < 10:
        print("⏳ Not enough data for drift check")
        return

    mae = mean_absolute_error(
        recent["actual_temperature"],
        recent["prediction"]
    )

    baseline_mae = load_baseline_mae()

    print(f"📊 Rolling MAE: {mae:.3f}")
    print(f"📏 Baseline MAE: {baseline_mae:.3f}")

    if mae > baseline_mae * DRIFT_MULTIPLIER:
        print("🚨 Drift detected — triggering retraining")
        retrain()
    else:
        print("✅ No drift detected")


def run_drift_monitor():
    print("🛰️ Drift monitor started")

    while True:
        try:
            check_drift()
        except Exception as e:
            print(f"❌ Drift monitor error: {e}")

        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    run_drift_monitor()
