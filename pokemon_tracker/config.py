import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "collection.db"
IMG_CACHE_DIR = BASE_DIR / "img_cache"

POKEMONTCG_API_KEY = os.getenv("POKEMONTCG_API_KEY", "")

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "pokemon-tracker-change-me")

UPDATE_INTERVAL_HOURS = int(os.getenv("UPDATE_INTERVAL_HOURS", "24"))
