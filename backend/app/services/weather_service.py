"""Weather Agent service.

Primary: Open-Meteo (free, no key) - 16-day daily forecast plus hourly rain probability, so the
itinerary can react to wet mornings/afternoons/evenings. Dates beyond the forecast horizon use
historical averages (clearly labelled).
Backup: met.no (Norwegian Meteorological Institute, free, no key, ~10 days). Open-Meteo rate-limits
shared cloud IPs such as Render's free tier; met.no gives rainfall amounts rather than probabilities
for India, so with met.no the rain chance is estimated from the forecast amount.
Last resort: OpenWeather (5-day, needs a key).
"""

import asyncio
import time
from datetime import date, datetime, timedelta, timezone

import httpx

from app.config import OPENWEATHER_API_KEY
from app.services.geo import get_json, locate

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TZ = "Asia/Kolkata"
FORECAST_HORIZON_DAYS = 15
HEAT_THRESHOLD_C = 36
RAIN_THRESHOLD_PCT = 60
CACHE_TTL_SECONDS = 1800
METNO_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
IST = timezone(timedelta(hours=5, minutes=30))
OPEN_METEO_COOLDOWN_SECONDS = 600
_open_meteo_blocked_until = 0.0

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
    data = await get_json(
        client,
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "hourly": "precipitation_probability",
            "timezone": TZ,
            "forecast_days": 16,
        },
    )
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


METNO_WORDS = {
    "clearsky": "clear sky", "fair": "mainly clear", "partlycloudy": "partly cloudy", "cloudy": "overcast",
    "fog": "fog", "lightrain": "light rain", "rain": "rain", "heavyrain": "heavy rain",
    "lightrainshowers": "light rain showers", "rainshowers": "rain showers", "heavyrainshowers": "heavy rain showers",
}


def _metno_condition(code: str) -> str:
    base = code.split("_")[0]
    if "thunder" in base:
        return "thunderstorm"
    return METNO_WORDS.get(base, base)


def _chance_from_mm(mm: float, window: bool) -> int:
    """Rough rain likelihood from forecast rainfall (met.no gives amounts, not probabilities, for India)."""
    steps = [(2, 75), (0.5, 55), (0.1, 30)] if window else [(10, 85), (5, 70), (2, 55), (0.5, 35), (0.05, 20)]
    return next((pct for limit, pct in steps if mm >= limit), 5)


async def _metno_forecast(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    key = ("metno", round(lat, 2), round(lon, 2))
    if (hit := _cached(key)) is not None:
        return hit
    data = await get_json(client, METNO_URL, {"lat": round(lat, 4), "lon": round(lon, 4)})
    hourly_mm: dict = {}
    temps: dict = {}
    codes: dict = {}
    for t in data["properties"]["timeseries"]:
        at = datetime.fromisoformat(t["time"].replace("Z", "+00:00")).astimezone(IST)
        d = t["data"]
        day = at.date().isoformat()
        temps.setdefault(day, []).append(d["instant"]["details"]["air_temperature"])
        if "next_1_hours" in d:
            hourly_mm[at] = d["next_1_hours"]["details"].get("precipitation_amount", 0) or 0
            codes.setdefault(day, []).append((at.hour, d["next_1_hours"]["summary"]["symbol_code"]))
        elif "next_6_hours" in d:
            six = d["next_6_hours"]
            for h in range(6):  # spread the 6-hour total so morning/afternoon/evening stay meaningful
                hourly_mm[at + timedelta(hours=h)] = (six["details"].get("precipitation_amount", 0) or 0) / 6
            for k in ("air_temperature_max", "air_temperature_min"):
                if k in six["details"]:
                    temps[day].append(six["details"][k])
            codes.setdefault(day, []).append((at.hour, six["summary"]["symbol_code"]))

    by_day: dict = {}
    for at, mm in hourly_mm.items():
        by_day.setdefault(at.date().isoformat(), []).append((at.hour, mm))

    out = {}
    for day, ts in temps.items():
        day_codes = codes.get(day)
        if not day_codes:
            continue
        hours = by_day.get(day, [])
        windows = {}
        for name, lo, hi in (("morning", 6, 11), ("afternoon", 12, 17), ("evening", 18, 21)):
            vals = [mm for h, mm in hours if lo <= h <= hi]
            windows[name] = _chance_from_mm(sum(vals), window=True) if vals else None
        total = sum(mm for _, mm in hours)
        midday = min(day_codes, key=lambda c: abs(c[0] - 13))[1]
        out[day] = {
            "date": day, "temp": round(max(ts)), "temp_max": round(max(ts)), "temp_min": round(min(ts)),
            "rain_probability": max([_chance_from_mm(total, window=False)] + [w for w in windows.values() if w is not None]),
            "precipitation_mm": round(total, 1), "condition": _metno_condition(midday),
            "thunderstorm": any("thunder" in c for _, c in day_codes), "windows": windows, "source": "forecast",
            "rain_estimated": True,
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
        d = (await get_json(client, ARCHIVE_URL, {
            "latitude": lat, "longitude": lon, "start_date": s.isoformat(), "end_date": e.isoformat(),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", "timezone": TZ,
        }))["daily"]
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


async def _openweather_fallback(client: httpx.AsyncClient, place: dict | None, city: str, trip_dates: list[str]) -> dict:
    if not place:
        geo = await client.get("https://api.openweathermap.org/geo/1.0/direct",
                               params={"q": city, "limit": 1, "appid": OPENWEATHER_API_KEY})
        geo.raise_for_status()
        found = geo.json()
        if not found:
            return {}
        place = {"lat": found[0]["lat"], "lon": found[0]["lon"]}
    resp = await client.get("https://api.openweathermap.org/data/2.5/forecast",
                            params={"lat": place["lat"], "lon": place["lon"], "appid": OPENWEATHER_API_KEY, "units": "metric"})
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

    global _open_meteo_blocked_until
    provider = None
    entries: dict = {}
    place = None
    errors: list = []
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            place = await locate(client, city)
        except Exception as exc:
            errors.append(exc)
        if place:
            fc_dates = [d for d in trip if today <= d <= horizon]
            other_dates = [d for d in trip if d not in fc_dates]
            open_meteo_ok = time.time() >= _open_meteo_blocked_until
            fc = None
            if fc_dates and open_meteo_ok:
                try:
                    fc, provider = await _forecast(client, place["lat"], place["lon"]), "open-meteo"
                except Exception as exc:
                    errors.append(exc)
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
                        _open_meteo_blocked_until = time.time() + OPEN_METEO_COOLDOWN_SECONDS
                        open_meteo_ok = False
            if fc_dates and fc is None:
                try:
                    fc, provider = await _metno_forecast(client, place["lat"], place["lon"]), "met.no"
                except Exception as exc:
                    errors.append(exc)
            if fc:
                entries.update({d.isoformat(): fc[d.isoformat()] for d in fc_dates if d.isoformat() in fc})
            if other_dates and open_meteo_ok:
                try:
                    entries.update(await _climatology(client, place["lat"], place["lon"], other_dates))
                    provider = provider or "open-meteo"
                except Exception as exc:
                    errors.append(exc)
        elif not errors:
            return {"available": False, "error": f"Could not locate '{city}' for weather."}

        if not entries and OPENWEATHER_API_KEY:
            try:
                entries, provider = await _openweather_fallback(client, place, city, trip_iso), "openweathermap"
            except Exception as exc:
                errors.append(exc)

    forecast = [entries[d] for d in trip_iso if d in entries]
    if not forecast:
        # Every live provider failed (e.g. rate limits): show typical seasonal conditions, clearly labelled.
        forecast, provider = [_seasonal(d) for d in trip], "seasonal estimate (live weather busy)"

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


# Typical (min, max, rain chance %) by month for peninsular and central India; used only as a last resort.
SEASONAL = {1: (15, 30, 5), 2: (17, 33, 5), 3: (21, 36, 5), 4: (24, 38, 10), 5: (25, 39, 20), 6: (23, 33, 60),
            7: (22, 30, 70), 8: (22, 30, 65), 9: (22, 31, 55), 10: (21, 31, 35), 11: (18, 29, 15), 12: (16, 28, 5)}


def _seasonal(d: date) -> dict:
    lo, hi, rain = SEASONAL[d.month]
    return {
        "date": d.isoformat(), "temp": hi, "temp_max": hi, "temp_min": lo, "rain_probability": rain,
        "precipitation_mm": None, "condition": f"typical for {d.strftime('%B')} (estimate)", "thunderstorm": False,
        "windows": {"morning": None, "afternoon": None, "evening": None}, "source": "climatology",
    }


def _friendly(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return "Live weather is busy right now (the free weather service is rate-limiting requests). Please try again in a minute."
    if isinstance(exc, httpx.TimeoutException):
        return "Live weather took too long to respond. Please try again in a moment."
    return f"Live weather is temporarily unavailable ({exc.__class__.__name__}). Please try again shortly."


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
