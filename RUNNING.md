# DHAROHAR CONNECT — How to Run

Two servers are required at the same time: the FastAPI backend (port 8000) and the
Vite/React frontend (port 5173).

---

## A) Already set up on this machine (quick start)

**Terminal 1 — Backend**

```bash
cd "D:/Projects/mnt/data/dharohar-connect-mvp/backend"
./venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

Backend runs at `http://127.0.0.1:8000`. API keys are already saved in `backend/.env`,
so Groq (LLM) and OpenWeather (live forecast) should be enabled automatically.

**Terminal 2 — Frontend**

```bash
cd "D:/Projects/mnt/data/dharohar-connect-mvp/frontend"
npm run dev
```

Frontend runs at `http://localhost:5173` — open that URL in your browser.

**Sanity check:** visit `http://127.0.0.1:8000/api/health`. It should return:

```json
{"status":"ok","app":"DHAROHAR CONNECT","groq_configured":true,"openweather_configured":true}
```

If either `_configured` field is `false`, the backend didn't load `.env` — stop it
(Ctrl+C) and start it again.

---

## B) Fresh setup on a teammate's laptop (nothing installed yet)

**Prerequisites:** Python 3.11+ and Node.js 18+ installed.

**Backend — one-time setup:**

```bash
cd dharohar-connect-mvp/backend
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

Create `backend/.env` (copy `backend/.env.example`) and fill in:

```
GROQ_API_KEY=<get a free key at console.groq.com>
GROQ_MODEL=openai/gpt-oss-120b
OPENWEATHER_API_KEY=<get a free key at openweathermap.org/api>
```

Then start it the same way as Terminal 1 in section A.

> Note: Travel routing (OSRM + Nominatim, OpenStreetMap) needs **no API key** — it
> works out of the box on any machine.

**Frontend — one-time setup:**

```bash
cd dharohar-connect-mvp/frontend
npm install
npm run dev
```

---

## C) Showing it on another device (phone, second laptop, same WiFi)

By default Vite only serves on `localhost`, which other devices on the network can't
reach. Restart the frontend exposed to the network instead:

```bash
npm run dev -- --host
```

This prints a `Network:` URL such as `http://192.168.x.x:5173` — open that on the
other device (it must be on the same WiFi network as this machine).

The other device also needs to reach the backend, not `localhost` on itself. Before
starting the frontend, set:

```bash
VITE_API_URL=http://192.168.x.x:8000/api npm run dev -- --host
```

(replace `192.168.x.x` with this machine's actual local IP address, e.g. from
`ipconfig` / `ifconfig`).

---

## D) Presentation-day checklist

- [ ] Start both servers **before** walking into the room — never demo
      `npm install` / `pip install` live.
- [ ] Confirm `/api/health` shows `groq_configured:true` and
      `openweather_configured:true`.
- [ ] Do one full live run-through beforehand: Plan Trip on a day with real rain in
      the forecast (confirms the weather-adaptive itinerary), and one AI Guide
      question (confirms live Groq answers, not fallback mode).
- [ ] If a teammate is presenting on their own laptop, make sure section B was done
      **the night before**, not at the venue.

---

## E) Database, accounts and bookings

- **Database:** SQLAlchemy. Defaults to a local SQLite file (`backend/dharohar.db`, created and
  seeded automatically on first start). For production set `DATABASE_URL` in `backend/.env` to a free
  hosted Postgres (Neon or Supabase) and `pip install psycopg2-binary`; no code changes needed.
- **Accounts:** email + password, PBKDF2-hashed, JWT sessions. `JWT_SECRET` is auto-generated to
  `backend/.jwt_secret` if not set (set your own in production).
- **Bookings:** hotel and monument-ticket bookings check real availability (date-overlap for rooms,
  daily capacity for tickets), support cancellation, and are stored per user. The inventory is
  **demo data** and payments are **simulated (test mode)** - integrate a hotel-provider API and a
  payment gateway before taking real bookings or money.
- **Groups, community posts, comments, likes, saved trips** are all stored in the database.
- **Weather:** Open-Meteo (free, no key): 16-day forecast with morning/afternoon/evening rain
  windows; dates beyond that use historical averages, clearly labelled. OpenWeather is only a fallback.
- **Tests:** `cd backend && ./venv/Scripts/python.exe -m pytest -q`
- **Production env:** set `CORS_ORIGINS` to your frontend URL and `VITE_API_URL` for the frontend build.

---

## F) Deploying to Render

A `render.yaml` blueprint is included at the project root, defining both services:

1. On [render.com](https://render.com), **New > Blueprint**, connect the `Dharohar_Connect` repo.
   Render reads `render.yaml` and creates both services automatically.
2. It will prompt for the env vars marked `sync: false` — fill in:
   - `GROQ_API_KEY`, `OPENWEATHER_API_KEY` — your keys
   - `DATABASE_URL` — see the database note below; do not leave this on SQLite
   - `CORS_ORIGINS` — the frontend's Render URL once it's assigned (you can redeploy the
     backend once you know it), e.g. `https://dharohar-frontend.onrender.com`
   - `VITE_API_URL` — the backend's Render URL, e.g. `https://dharohar-backend.onrender.com/api`
   - `JWT_SECRET` is auto-generated by Render; you don't need to set it.

**Database — do this before relying on the deployment:** Render's web services have an
ephemeral filesystem, so the default local SQLite file gets wiped on every deploy/restart
and isn't shared if Render ever runs more than one instance. Use a real hosted Postgres via
`DATABASE_URL`. Render's own free Postgres **expires 30 days after creation** (14-day grace
period, then it's deleted with all data) — fine for a demo window, risky if your event runs
longer. [Neon](https://neon.tech) or [Supabase](https://supabase.com) free tiers don't have
that expiry and work as a drop-in `DATABASE_URL` with no code changes.

**Free-tier cold starts:** a free Render web service spins down after 15 minutes idle and
takes about a minute to wake on the next request. Open the app yourself a few minutes before
a live demo so the mentor doesn't hit that delay on the first click.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| AI Guide answer says `"LOCAL KNOWLEDGE FALLBACK"` instead of using Groq | `.env` key not loaded, or Groq API error | Restart the backend process; check `/api/health` |
| Trip planner shows "Live weather unavailable" | `OPENWEATHER_API_KEY` missing/invalid | Check `backend/.env`, restart backend |
| Trip planner shows "Route unavailable" | Nominatim/OSRM couldn't geocode a place name | Try a more specific place name (e.g. "Pune, India") |
| Frontend can't reach backend (`Could not reach backend`) | Backend not running, or wrong port | Confirm Terminal 1 is running and `/api/health` responds |
| Port already in use | Another process is using 8000 or 5173 | Add `--port <other-port>` to uvicorn, or stop the other process |
