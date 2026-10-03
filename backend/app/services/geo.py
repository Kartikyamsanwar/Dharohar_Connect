"""Geocoding shared by the Weather and Travel agents.

Order: built-in table of destination and major Indian cities (no network), heritage site names
mapped to their city, Open-Meteo geocoding, then Nominatim. The free public geocoders throttle
cloud hosts that share outgoing IPs (e.g. Render's free tier), so the table keeps normal trips
working without them; results from the network are cached.
"""

import asyncio
import json
from pathlib import Path

import httpx

from app.data_loader import SITE_CITY, resolve_site

UA = {"User-Agent": "DharoharConnect/1.0 (https://github.com/Kartikyamsanwar/Dharohar_Connect)"}
OPEN_METEO_GEO = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

_data = json.loads((Path(__file__).resolve().parents[1] / "data" / "places.json").read_text(encoding="utf-8"))
PLACES = {name.lower(): {"name": name, **v} for name, v in _data["places"].items()}
ALIASES = _data["aliases"]
_cache: dict = {}


def _key(place: str) -> str:
    return place.split(",")[0].strip().lower()


def lookup(place: str) -> dict | None:
    """Offline lookup: a known city, an alias, or a heritage site's city."""
    key = _key(place)
    if key in PLACES:
        return PLACES[key]
    if key in ALIASES:
        return PLACES[ALIASES[key].lower()]
    site = resolve_site(place)
    if site and SITE_CITY.get(site["id"], "").lower() in PLACES:
        return PLACES[SITE_CITY[site["id"]].lower()]
    return None


async def get_json(client: httpx.AsyncClient, url: str, params: dict, retries: int = 2):
    """GET with a short backoff on rate limits and server errors."""
    for attempt in range(retries + 1):
        resp = await client.get(url, params=params, headers=UA)
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
            await asyncio.sleep(1.5 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()


async def locate(client: httpx.AsyncClient, place: str) -> dict | None:
    """Return {"name", "lat", "lon", "state"} for a place in India, or None if not found."""
    if not place or not place.strip():
        return None
    known = lookup(place)
    if known:
        return known
    key = _key(place)
    if key in _cache:
        return _cache[key]

    data = await get_json(client, OPEN_METEO_GEO, {"name": place.split(",")[0].strip(), "count": 1, "language": "en", "countryCode": "IN"})
    res = (data.get("results") or [None])[0]
    if res:
        found = {"name": res.get("name", place), "lat": res["latitude"], "lon": res["longitude"], "state": res.get("admin1", "")}
    else:
        rows = await get_json(client, NOMINATIM, {"q": place, "format": "json", "limit": 1, "countrycodes": "in"})
        found = {"name": place.strip(), "lat": float(rows[0]["lat"]), "lon": float(rows[0]["lon"]), "state": ""} if rows else None
    if found:
        _cache[key] = found
    return found
