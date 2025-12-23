import os
import sys
import time
from datetime import datetime


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from orchestration.retrain_pipeline import retrain


RETRAIN_INTERVAL_HOURS = 24   # daily retraining


def run_scheduler():
    print("🕒 Retraining scheduler started")
    print(f"🔁 Interval: every {RETRAIN_INTERVAL_HOURS} hours")

    while True:
        start_time = datetime.now()
        print(f"\n⏰ Retraining triggered at {start_time}")

        try:
            retrain()
        except Exception as e:
            print(f"❌ Retraining failed: {e}")

        print("🛌 Sleeping until next retrain cycle...\n")
        time.sleep(RETRAIN_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    run_scheduler()
