## Imports all configuration from environment variables

import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DB_URL")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")