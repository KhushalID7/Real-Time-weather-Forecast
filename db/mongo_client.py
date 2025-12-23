import os
import sys
from pymongo import MongoClient
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

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "weather_ml")

if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI not found in .env")

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[DB_NAME]
