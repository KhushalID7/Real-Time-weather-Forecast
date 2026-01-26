import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.mongo_client import get_db

def reset_predictions():
    db = get_db()
    col = db["predictions"]

    result = col.delete_many({})
    print(f"🧹 Deleted {result.deleted_count} documents_toggle from predictions collection")

if __name__ == "__main__":
    reset_predictions()
