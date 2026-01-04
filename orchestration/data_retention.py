import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

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


# -------------------------------------------------
# Configuration
# -------------------------------------------------
RETENTION_DAYS = 90  # Keep predictions for 90 days
# Set to smaller value (e.g., 30) for aggressive cleanup on free tier


# -------------------------------------------------
# Data Retention Logic
# -------------------------------------------------
def cleanup_old_predictions():
    """
    Delete old predictions from MongoDB to keep database size bounded.
    Keeps rolling window of recent predictions for drift monitoring.
    """
    db = get_db()
    predictions_col = db["predictions"]

    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)

    result = predictions_col.delete_many({
        "created_at": {"$lt": cutoff}
    })

    deleted_count = result.deleted_count

    if deleted_count > 0:
        print(f"🧹 Deleted {deleted_count} old predictions (older than {RETENTION_DAYS} days)")
    else:
        print(f"✅ No predictions older than {RETENTION_DAYS} days to delete")

    # Optional: Print collection size
    try:
        collection_stats = db.command("collstats", "predictions")
        storage_mb = collection_stats.get("size", 0) / (1024 * 1024)
        doc_count = collection_stats.get("count", 0)
        print(f"   📊 Predictions collection: {doc_count} docs, {storage_mb:.2f} MB")
    except Exception as e:
        print(f"   ⚠️ Could not fetch stats: {e}")


if __name__ == "__main__":
    cleanup_old_predictions()
