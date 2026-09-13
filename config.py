import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# INTERNAL_DATABASE_URL'dan parse qilish (Render uchun)
DATABASE_URL = os.getenv("INTERNAL_DATABASE_URL", "")

if DATABASE_URL:
    # postgresql://user:password@host:port/dbname
    parsed = urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname or "localhost"
    DB_PORT = parsed.port or 5432
    DB_NAME = parsed.path.lstrip('/') if parsed.path else "testbot"
    DB_USER = parsed.username or "postgres"
    DB_PASSWORD = parsed.password or ""
else:
    # Fallback (agar DATABASE_URL bo'lmasa)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "testbot")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
