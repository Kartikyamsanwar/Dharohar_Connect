# DHAROHAR CONNECT

**Connecting People with India's Heritage.**

An AI-powered heritage discovery and travel-planning platform built for **Smart India Hackathon 2026** (Problem Statement ID: SIH26197, Theme: Heritage & Culture, Team: Garuda).

DHAROHAR CONNECT brings together a curated, source-verified heritage knowledge base, a multi-agent AI trip planner that reacts to live weather and real road routing, hotel and monument-ticket booking, and a community layer for heritage travellers — all in one platform, instead of scattered across government portals, travel apps and unverified blogs.

---

## What it does

- **Explore heritage** — 27 curated Indian heritage sites across 15+ states, each with period, significance and verified sources (Archaeological Survey of India, UNESCO World Heritage Centre).
- **AI Heritage Guide** — a conversational, tool-using agent. It answers from the curated, source-verified records (and labels anything beyond them as general knowledge), calls live tools to check the weather at a site or estimate a trip's cost from your city, asks a clarifying question when a request is too vague, remembers the conversation, and hands off to the Trip Planner or Booking with your details pre-filled.
- **AI Trip Planner** — a multi-agent pipeline plans a day-wise itinerary from live weather and live road routing, and adapts the schedule around rain or heat automatically.
- **Book stays and tickets** — real availability logic (date-overlap for hotel rooms, daily capacity for monument tickets), booking references, and cancellation. Inventory is demo data and payments run in test mode.
- **Groups** — join or create a travel group, ranked by a match score computed from destination, budget and shared interests.
- **Community** — share heritage stories and experiences, comment, like.
- **Safety Center** — trip-safety guidance, checklists, and weather-aware precautions.

## How the AI planner works

A LangGraph state graph coordinates specialised agents, each with a narrow responsibility, sharing one trip-planning state:

```
Orchestrator (entry point)
   ├─→ Heritage Agent    curated knowledge base
   ├─→ Weather Agent     Open-Meteo, 16-day forecast + morning/afternoon/evening rain windows
   ├─→ Travel Agent      OpenStreetMap geocoding + road routing        (all three run in parallel)
         ↓
   Recommendation Agent  Groq LLM reasons over heritage + weather + travel + budget
         ↓
   Itinerary Agent       day-wise schedule; the wet or hot part of a day is moved indoors automatically
         ↓
   Safety Agent          context-aware safety tips
```

The itinerary genuinely reorganises itself around real forecast data — if a day's afternoon has a high rain probability, that slot (and only that slot) is swapped for an indoor activity.

## Tech stack

**Built and working now:**

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI, SQLAlchemy |
| Agent orchestration | LangGraph |
| LLM inference | Groq (`openai/gpt-oss-120b`) |
| Knowledge retrieval | RAG over a curated, source-verified JSON knowledge base (keyword-based retrieval, not vector/embedding search) |
| Live weather | Open-Meteo — free, no API key |
| Live routing | OpenStreetMap — Nominatim (geocoding) + OSRM (routing), free, no API key |
| Database | SQLite for development; PostgreSQL-ready for production via `DATABASE_URL`, no code change |
| Auth | Email/password, PBKDF2-hashed, JWT sessions |
| Testing | Pytest |

**Planned next:** vector-embedding semantic search, hosted PostgreSQL in production, containerized deployment, multilingual and voice interface, computer-vision monument recognition.

## Project structure

```
backend/
  app/
    agents/      orchestrator + the six trip-planning agents, and the budget estimator
    routes/      FastAPI routers — auth, heritage, guide, trips, bookings, groups, community, culture, safety
    services/    llm_service (Groq), weather_service (Open-Meteo), travel_service (OSM), booking_service
    models.py    SQLAlchemy models
    seed.py      seeds hotels/tickets/groups/community posts on first run
  tests/         pytest suite
  render.yaml    Render deployment blueprint (see repo root)

frontend/
  src/
    pages/       Home, Explore, Guide, Planner, Book, MyTrips, Groups, Community, Culture, Safety
    components/  Header, Detail modal, Auth
    lib/api.js   backend API client
```

## Getting started

```bash
# Backend
cd backend
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY and OPENWEATHER_API_KEY
./venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Full setup (fresh machine, network access for other devices, deployment, troubleshooting) is in **[RUNNING.md](RUNNING.md)**.

## Deploying

A `render.yaml` blueprint at the repo root provisions both the backend and frontend as separate Render services. See **[RUNNING.md § Deploying to Render](RUNNING.md#f-deploying-to-render)** for the full walkthrough, including the database and cold-start notes that matter for this app specifically.

## Testing

```bash
cd backend
./venv/Scripts/python.exe -m pytest -q
```

## Image credits

Heritage site photos are from Wikimedia Commons and are used under their individual licences (CC BY, CC BY-SA, GFDL or public domain). Each photo's author, licence and source link are stored in `backend/app/data/heritage.json` and shown in the app on the site's detail view.

## Known limitations

- RAG retrieval is keyword-based, not vector/embedding-based.
- Hotel and ticket inventory is demo data; payments are simulated (test mode).
- Groups have no identity verification yet.
- Agent routing between the planning agents is fixed at build time, not chosen dynamically by the LLM.

## Team

Team Garuda — Smart India Hackathon 2026, Problem Statement SIH26197, Heritage & Culture.
