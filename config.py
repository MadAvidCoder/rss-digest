## Imports all configuration from environment variables

import os
from dotenv import load_dotenv

load_dotenv()

def _bool(v, default=False):
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "on")

def _int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except Exception:
        return None


DB_URL = os.environ.get("DB_URL")

EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = [e.strip() for e in os.environ.get("EMAIL_TO", "").split(",") if e.strip()]

SMTP_USERNAME = os.environ.get("SMTP_USERNAME")

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

FROM_NAME = os.environ.get("FROM_NAME", "RSS Digest")
SUBJECT_PREFIX = os.environ.get("SUBJECT_PREFIX", "[RSS Digest]")

DEBUG = _bool(os.environ.get("DEBUG"), False)

SEND_INDIVIDUALLY = _bool(os.environ.get("SEND_INDIVIDUALLY"), False)
USE_BCC = _bool(os.environ.get("USE_BCC"), True)

DRY_RUN = _bool(os.environ.get("DRY_RUN"), True)
SKIP_SMTP_AUTH = _bool(os.environ.get("SKIP_SMTP_AUTH"), False)

MAX_ENTRIES_PER_FEED = _int_or_none(os.environ.get("MAX_ENTRIES_PER_FEED"))
MAX_ITEMS = _int_or_none(os.environ.get("MAX_ITEMS"))

FEED_URLS = [u.strip() for u in os.environ.get("FEED_URLS", "").split(",") if u.strip()]

TEST_EMAIL = os.environ.get("TEST_EMAIL")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")