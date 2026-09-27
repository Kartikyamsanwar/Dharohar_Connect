import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# SQLite by default; set to a free hosted Postgres URL (Neon / Supabase) in production, e.g.
# postgresql+psycopg2://user:pass@host/dbname
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'dharohar.db').as_posix()}")

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "72"))


def _jwt_secret() -> str:
    env = os.getenv("JWT_SECRET")
    if env:
        return env
    path = BASE_DIR / ".jwt_secret"
    if path.exists():
        return path.read_text().strip()
    secret = secrets.token_urlsafe(48)
    path.write_text(secret)
    return secret


JWT_SECRET = _jwt_secret()
