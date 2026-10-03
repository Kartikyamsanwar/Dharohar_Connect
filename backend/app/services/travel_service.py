"""Travel/Route Agent: road distance and drive time between two places.

Live routing comes from the public OSRM server. If it is unreachable or rate-limited, the agent
falls back to an estimate from straight-line distance and says so, so a plan never loses its
transport cost just because a free API is busy.
"""

import math

import httpx

from app.services.geo import UA, locate

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
ROAD_FACTOR = 1.25        # typical ratio of Indian road distance to straight-line distance
AVG_SPEED_KMH = 55        # realistic average including highways and towns
_routes: dict = {}


def _haversine_km(a: dict, b: dict) -> float:
    r = 6371.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _unavailable(origin: str, destination: str, note: str) -> dict:
    return {"available": False, "origin": origin, "destination": destination, "note": note}


async def get_route(origin: str, destination: str) -> dict:
    if not origin.strip() or not destination.strip():
        return _unavailable(origin, destination, "Provide both a starting location and a destination for route planning.")

    async with httpx.AsyncClient(timeout=12) as client:
        try:
            a = await locate(client, origin)
            b = await locate(client, destination)
        except Exception as exc:
            return _unavailable(origin, destination, f"Map lookup is busy right now, please try again shortly ({exc.__class__.__name__}).")
        if not a or not b:
            return _unavailable(origin, destination, f"Could not locate '{origin if not a else destination}' on the map.")

        key = (round(a["lat"], 3), round(a["lon"], 3), round(b["lat"], 3), round(b["lon"], 3))
        if key in _routes:
            return {**_routes[key], "origin": origin, "destination": destination}

        try:
            resp = await client.get(f"{OSRM_URL}/{a['lon']},{a['lat']};{b['lon']},{b['lat']}",
                                    params={"overview": "false"}, headers=UA)
            resp.raise_for_status()
            best = (resp.json().get("routes") or [None])[0]
        except Exception:
            best = None

    if best:
        distance_km = round(best["distance"] / 1000, 1)
        duration_hours = round(best["duration"] / 3600, 1)
        result = {"available": True, "estimated": False, "distance_km": distance_km, "duration_hours": duration_hours,
                  "note": f"Approx. {distance_km} km, {duration_hours} hr by road (live route via OSRM)."}
        _routes[key] = result
    else:
        distance_km = round(_haversine_km(a, b) * ROAD_FACTOR, 1)
        duration_hours = round(distance_km / AVG_SPEED_KMH, 1)
        result = {"available": True, "estimated": True, "distance_km": distance_km, "duration_hours": duration_hours,
                  "note": f"About {distance_km} km, {duration_hours} hr by road (estimated; live routing is busy right now)."}
    return {**result, "origin": origin, "destination": destination}
