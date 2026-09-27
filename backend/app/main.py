from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, DATABASE_URL, GROQ_API_KEY, OPENWEATHER_API_KEY
from app.db import init_db
from app.routes import auth, bookings, community, culture, groups, guide, heritage, safety, trips
from app.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="DHAROHAR CONNECT API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (heritage, guide, trips, community, groups, culture, safety, auth, bookings):
    app.include_router(r.router, prefix="/api")


@app.get("/api/health")
def health():
    from sqlalchemy import text

    from app.db import engine
    from app.services.llm_service import is_llm_available

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "app": "DHAROHAR CONNECT",
        "groq_configured": is_llm_available(),
        "openweather_configured": bool(OPENWEATHER_API_KEY),
        "weather_provider": "open-meteo (primary, no key needed)" + (" + openweathermap fallback" if OPENWEATHER_API_KEY else ""),
        "database": DATABASE_URL.split(":")[0].split("+")[0],
        "database_ok": db_ok,
    }
