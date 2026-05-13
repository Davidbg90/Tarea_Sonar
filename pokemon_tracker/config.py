import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "collection.db"

CARDMARKET_APP_TOKEN = os.getenv("CARDMARKET_APP_TOKEN", "")
CARDMARKET_APP_SECRET = os.getenv("CARDMARKET_APP_SECRET", "")
CARDMARKET_ACCESS_TOKEN = os.getenv("CARDMARKET_ACCESS_TOKEN", "")
CARDMARKET_ACCESS_SECRET = os.getenv("CARDMARKET_ACCESS_SECRET", "")
CARDMARKET_SANDBOX = os.getenv("CARDMARKET_SANDBOX", "false").lower() == "true"

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "pokemon-tracker-change-me")

UPDATE_INTERVAL_HOURS = int(os.getenv("UPDATE_INTERVAL_HOURS", "24"))
