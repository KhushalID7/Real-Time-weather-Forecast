import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.mongo_client import get_db

db = get_db()
col = db["predictions"]
col.create_index("created_at")
col.create_index("timestamp")
col.create_index("actual_temperature")
print("Indexes created")