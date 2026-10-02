"""Weather Agent service.

Primary: Open-Meteo (free, no key) - 16-day daily forecast plus hourly rain probability, so the
itinerary can react to wet mornings/afternoons/evenings. Dates beyond the forecast horizon use
historical averages (clearly labelled). OpenWeather (5-day) is used only as a fallback.
"""

import asyncio
import time
from datetime import date, datetime, timedelta

import httpx

from app.config import OPENWEATHER_API_KEY
from app.services.travel_service import geocode

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TZ = "Asia/Kolkata"
FORECAST_HORIZON_DAYS = 15
HEAT_THRESHOLD_C = 36
RAIN_THRESHOLD_PCT = 60
CACHE_TTL_SECONDS = 1800

WMO = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain", 66: "freezing rain", 67: "freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains",
    80: "light rain showers", 81: "rain showers", 82: "violent rain showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with heavy hail",
}

_cache: dict = {}


def _cached(key):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    return None


def _store(key, value):
    _cache[key] = (time.time(), value)
    return value


def _parse_start(start_date: str) -> date:
    try:
        return date.fromisoformat(start_date)
    except (TypeError, ValueError):
        return date.today()


async def _geocode(client: httpx.AsyncClient, city: str):
    key = ("geo", city.lower().strip())
    if (hit := _cached(key)) is not None:
        return hit
    resp = await client.get(
        GEO_URL, params={"name": city, "count": 1, "language": "en", "countryCode": "IN"}
    )
    resp.raise_for_status()
    results = resp.json().get("results") or []
    if results:
        r = results[0]
        return _store(key, {"lat": r["latitude"], "lon": r["longitude"], "name": r.get("name", city), "state": r.get("admin1", "")})
    # Open-Meteo's gazetteer misses some small heritage villages (e.g. Dholavira, Nalanda); OSM has them.
    coords = await geocode(client, city)
    if not coords:
        return None
    return _store(key, {"lat": coords[0], "lon": coords[1], "name": city, "state": ""})


def _window_max(hourly_times, hourly_probs, day: str, start_h: int, end_h: int):
    vals = []
    for t, p in zip(hourly_times, hourly_probs):
        if p is None or not t.startswith(day):
            continue
        if start_h <= int(t[11:13]) <= end_h:
            vals.append(p)
    return max(vals) if vals else None


async def _forecast(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    key = ("fc", round(lat, 2), round(lon, 2))
    if (hit := _cached(key)) is not None:
        return hit
    resp = await client.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "hourly": "precipitation_probability",
            "timezone": TZ,
            "forecast_days": 16,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    daily, hourly = data["daily"], data["hourly"]
    out = {}
    for i, day in enumerate(daily["time"]):
        precip = daily["precipitation_sum"][i] or 0
        prob = daily["precipitation_probability_max"][i]
        if prob is None:
            prob = 60 if precip >= 5 else 20 if precip >= 1 else 5
        code = daily["weathercode"][i]
        out[day] = {
            "date": day,
            "temp": round(daily["temperature_2m_max"][i]),
            "temp_max": round(daily["temperature_2m_max"][i]),
            "temp_min": round(daily["temperature_2m_min"][i]),
            "rain_probability": round(prob),
            "precipitation_mm": round(precip, 1),
            "condition": WMO.get(code, "unsettled"),
            "thunderstorm": code in (95, 96, 99),
            "windows": {
                "morning": _window_max(hourly["time"], hourly["precipitation_probability"], day, 6, 11),
                "afternoon": _window_max(hourly["time"], hourly["precipitation_probability"], day, 12, 17),
                "evening": _window_max(hourly["time"], hourly["precipitation_probability"], day, 18, 21),
            },
            "source": "forecast",
        }
    return _store(key, out)


async def _climatology(client: httpx.AsyncClient, lat: float, lon: float, days: list[date]) -> dict:
    """Average of the same calendar days in the previous 3 years."""
    if not days:
        return {}
    lo, hi = min(days), max(days)

    async def one_year(offset: int):
        try:
            s, e = lo.replace(year=lo.year - offset), hi.replace(year=hi.year - offset)
        except ValueError:
            return {}
        resp = await client.get(
            ARCHIVE_URL,
            params={
                "latitude": lat, "longitude": lon, "start_date": s.isoformat(), "end_date": e.isoformat(),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", "timezone": TZ,
            },
        )
        resp.raise_for_status()
        d = resp.json()["daily"]
        return {t[5:]: (d["temperature_2m_max"][i], d["temperature_2m_min"][i], d["precipitation_sum"][i] or 0)
                for i, t in enumerate(d["time"])}

    years = [y for y in await asyncio.gather(*(one_year(o) for o in (1, 2, 3)), return_exceptions=True) if isinstance(y, dict)]
    out = {}
    for d in days:
        samples = [y[d.isoformat()[5:]] for y in years if d.isoformat()[5:] in y and y[d.isoformat()[5:]][0] is not None]
        if not samples:
            continue
        wet = sum(1 for s in samples if s[2] >= 2.5)
        prob = round(100 * wet / len(samples))
        tmax = round(sum(s[0] for s in samples) / len(samples))
        out[d.isoformat()] = {
            "date": d.isoformat(),
            "temp": tmax, "temp_max": tmax,
            "temp_min": round(sum(s[1] for s in samples) / len(samples)),
            "rain_probability": prob,
            "precipitation_mm": round(sum(s[2] for s in samples) / len(samples), 1),
            "condition": f"typically {'wet' if prob >= RAIN_THRESHOLD_PCT else 'mostly dry'} (historical average)",
            "thunderstorm": False,
            "windows": {"morning": None, "afternoon": None, "evening": None},
            "source": "climatology",
        }
    return out


async def _openweather_fallback(client: httpx.AsyncClient, city: str, trip_dates: list[str]) -> dict:
    geo = await client.get("https://api.openweathermap.org/geo/1.0/direct",
                           params={"q": city, "limit": 1, "appid": OPENWEATHER_API_KEY})
    geo.raise_for_status()
    places = geo.json()
    if not places:
        return {}
    resp = await client.get("https://api.openweathermap.org/data/2.5/forecast",
                            params={"lat": places[0]["lat"], "lon": places[0]["lon"], "appid": OPENWEATHER_API_KEY, "units": "metric"})
    resp.raise_for_status()
    daily: dict = {}
    for item in resp.json().get("list", []):
        daily.setdefault(item["dt_txt"][:10], {"t": [], "p": [], "c": []})
        daily[item["dt_txt"][:10]]["t"].append(item["main"]["temp"])
        daily[item["dt_txt"][:10]]["p"].append(float(item.get("pop", 0)) * 100)
        daily[item["dt_txt"][:10]]["c"].append(item["weather"][0]["description"])
    out = {}
    for day in trip_dates:
        v = daily.get(day)
        if v:
            out[day] = {
                "date": day, "temp": round(max(v["t"])), "temp_max": round(max(v["t"])), "temp_min": round(min(v["t"])),
                "rain_probability": round(max(v["p"])), "precipitation_mm": None,
                "condition": max(set(v["c"]), key=v["c"].count), "thunderstorm": False,
                "windows": {"morning": None, "afternoon": None, "evening": None}, "source": "forecast",
            }
    return out


async def get_weather(city: str, start_date: str, days: int) -> dict:
    start = _parse_start(start_date)
    days = max(min(int(days), 30), 1)
    trip = [start + timedelta(days=i) for i in range(days)]
    trip_iso = [d.isoformat() for d in trip]
    today = date.today()
    horizon = today + timedelta(days=FORECAST_HORIZON_DAYS)

    provider = "open-meteo"
    entries: dict = {}
    place = None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            place = await _geocode(client, city)
            if not place:
                return {"available": False, "error": f"Could not locate '{city}' for weather."}
            fc_dates = [d for d in trip if today <= d <= horizon]
            other_dates = [d for d in trip if d not in fc_dates]
            if fc_dates:
                fc = await _forecast(client, place["lat"], place["lon"])
                entries.update({d.isoformat(): fc[d.isoformat()] for d in fc_dates if d.isoformat() in fc})
            entries.update(await _climatology(client, place["lat"], place["lon"], other_dates))
    except Exception as exc:
        if not OPENWEATHER_API_KEY:
            return {"available": False, "error": f"Weather service unreachable: {exc}"}
        try:
            provider = "openweathermap"
            async with httpx.AsyncClient(timeout=15) as client:
                entries = await _openweather_fallback(client, city, trip_iso)
        except Exception as exc2:
            return {"available": False, "error": f"Weather services unreachable: {exc2}"}

    forecast = [entries[d] for d in trip_iso if d in entries]
    if not forecast:
        return {"available": False, "error": "No weather data available for these dates."}

    live = [f for f in forecast if f["source"] == "forecast"]
    hist = [f for f in forecast if f["source"] == "climatology"]
    return {
        "available": True,
        "provider": provider,
        "city": city,
        "location": place,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "forecast": forecast,
        "live_days": len(live),
        "historical_days": len(hist),
        "planning_impact": _build_planning_impact(forecast, len(hist)),
    }


def _build_planning_impact(forecast: list, historical_days: int = 0) -> list[str]:
    impacts: list[str] = []
    rainy = [f for f in forecast if f.get("rain_probability", 0) >= RAIN_THRESHOLD_PCT]
    hot = [f for f in forecast if f.get("temp_max", f.get("temp", 0)) >= HEAT_THRESHOLD_C]
    stormy = [f for f in forecast if f.get("thunderstorm")]

    if rainy:
        impacts.append(
            f"Rain likely on {', '.join(f['date'] for f in rainy)} - outdoor monuments are scheduled in the driest "
            "part of those days and indoor museums fill the wet windows."
        )
    if hot:
        impacts.append(
            f"Very hot on {', '.join(f['date'] for f in hot)} (>= {HEAT_THRESHOLD_C} C) - outdoor visits are moved "
            "to early morning and evening."
        )
    if stormy:
        impacts.append(f"Thunderstorm risk on {', '.join(f['date'] for f in stormy)} - avoid exposed hilltops and open ruins.")
    if not impacts:
        impacts.append("Conditions look favourable for balanced outdoor heritage exploration with standard precautions.")
    if historical_days:
        impacts.append(
            f"{historical_days} day(s) are beyond the 16-day forecast, so they use historical averages; "
            "re-plan closer to departure for live weather."
        )
    return impacts
