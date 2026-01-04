import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from orchestration.backfill_actuals import backfill_actuals
from orchestration.drift_monitor import check_drift
from orchestration.data_retention import cleanup_old_predictions
from orchestration.retrain_pipeline import retrain


BACKFILL_INTERVAL_MIN = 60
DRIFT_CHECK_INTERVAL_MIN = 60
RETENTION_INTERVAL_HOURS = 24
RETRAIN_INTERVAL_HOURS = 24  # Optional safety retrain


last_backfill = None
last_drift_check = None
last_retention = None
last_retrain = None


def run_scheduler():
    """
    Main orchestration loop.
    Runs all jobs at specified intervals.
    Handles exceptions gracefully to prevent service crashes.
    """
    global last_backfill, last_drift_check, last_retention, last_retrain

    print("=" * 60)
    print("🕒 ML Orchestration Scheduler STARTED")
    print("🚀 Deployment-ready background services running")
    print("=" * 60)
    print()
    print(f"⚙️  Configuration:")
    print(f"   • Backfill: every {BACKFILL_INTERVAL_MIN} min")
    print(f"   • Drift check: every {DRIFT_CHECK_INTERVAL_MIN} min")
    print(f"   • Retention cleanup: every {RETENTION_INTERVAL_HOURS}h")
    print(f"   • Retraining: every {RETRAIN_INTERVAL_HOURS}h")
    print()

    while True:
        now = datetime.utcnow()

        try:
            # -----------------------------
            # Backfill actual temperatures
            # -----------------------------
            if last_backfill is None or (now - last_backfill) >= timedelta(minutes=BACKFILL_INTERVAL_MIN):
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 🔁 Running backfill job")
                try:
                    backfill_actuals()
                    last_backfill = now
                except Exception as e:
                    print(f"   ❌ Backfill error: {e}")

            # -----------------------------
            # Drift detection
            # -----------------------------
            if last_drift_check is None or (now - last_drift_check) >= timedelta(minutes=DRIFT_CHECK_INTERVAL_MIN):
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 📊 Running drift check")
                try:
                    check_drift()
                    last_drift_check = now
                except Exception as e:
                    print(f"   ❌ Drift check error: {e}")

            # -----------------------------
            # Data retention (MongoDB cleanup)
            # -----------------------------
            if last_retention is None or (now - last_retention) >= timedelta(hours=RETENTION_INTERVAL_HOURS):
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 🧹 Running data retention cleanup")
                try:
                    cleanup_old_predictions()
                    last_retention = now
                except Exception as e:
                    print(f"   ❌ Retention error: {e}")

            # -----------------------------
            # Time-based retraining (optional)
            # -----------------------------
            if last_retrain is None or (now - last_retrain) >= timedelta(hours=RETRAIN_INTERVAL_HOURS):
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Running scheduled retraining")
                try:
                    retrain()
                    last_retrain = now
                except Exception as e:
                    print(f"   ❌ Retrain error: {e}")

        except Exception as e:
            print(f"❌ Scheduler error: {e}")

        # Sleep small, check often (every 60 seconds)
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
