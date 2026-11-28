"""Application settings, read from environment variables (.env supported)."""
import logging
import os
import re
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("quest_portal")

BASE_DIR = Path(__file__).resolve().parent


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


class Settings:
    APP_NAME = "QUEST IT Portal"
    UNIVERSITY = "Quaid-e-Awam University of Engineering, Science & Technology, Nawabshah"
    DEPARTMENT = "Department of Information Technology"

    # SQLite for local development; set to a postgresql+psycopg2:// URL in production.
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'quest_portal.db'}")

    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
    TOKEN_TTL_MINUTES = _int("TOKEN_TTL_MINUTES", 60 * 8)
    ALGORITHM = "HS256"

    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if o.strip()
    ]

    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
    MAX_RECEIPT_BYTES = _int("MAX_RECEIPT_MB", 5) * 1024 * 1024
    ALLOWED_RECEIPT_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}

    # Roll number pattern, e.g. 21IT-95 (batch year, programme code, serial).
    ROLL_NO_PATTERN = re.compile(os.getenv("ROLL_NO_PATTERN", r"^\d{2}[A-Z]{2,4}-\d{1,3}$"))
    CHALLAN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-/]{2,39}$")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    FEE_CATEGORIES = [
        "Semester Tuition Fee",
        "Examination Fee",
        "Subject Improvement / Repeat Fee",
        "Hostel Fee",
        "Transport Fee",
        "Clearance / Degree Fee",
    ]
    CUSTOM_CATEGORY = "Custom"


settings = Settings()
if not os.getenv("SECRET_KEY"):
    log.warning("SECRET_KEY not set: using a random key, sessions reset on restart.")
