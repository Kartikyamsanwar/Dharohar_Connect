"""Travel/Route Agent — live geocoding + routing via free, keyless OSM services."""

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
HEADERS = {"User-Agent": "DharoharConnect/1.0 (https://github.com/Kartikyamsanwar/Dharohar_Connect)"}


async def geocode(client: httpx.AsyncClient, place: str):
    resp = await client.get(
        NOMINATIM_URL,
        params={"q": place, "format": "json", "limit": 1, "countrycodes": "in"},
        headers=HEADERS,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


async def get_route(origin: str, destination: str) -> dict:
    if not origin.strip() or not destination.strip():
        return {
            "available": False,
            "origin": origin,
            "destination": destination,
            "note": "Provide both a starting location and a destination for route planning.",
        }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            origin_coords = await geocode(client, origin)
            dest_coords = await geocode(client, destination)
            if not origin_coords or not dest_coords:
                missing = origin if not origin_coords else destination
                return {
                    "available": False,
                    "origin": origin,
                    "destination": destination,
                    "note": f"Could not locate '{missing}' on the map.",
                }

            olat, olon = origin_coords
            dlat, dlon = dest_coords
            route_resp = await client.get(
                f"{OSRM_URL}/{olon},{olat};{dlon},{dlat}",
                params={"overview": "false"},
                headers=HEADERS,
            )
            route_resp.raise_for_status()
            data = route_resp.json()
    except Exception as exc:
        return {
            "available": False,
            "origin": origin,
            "destination": destination,
            "note": f"Live route lookup failed: {exc}",
        }

    routes = data.get("routes") or []
    if not routes:
        return {
            "available": False,
            "origin": origin,
            "destination": destination,
            "note": "No driving route found between these locations.",
        }

    best = routes[0]
    distance_km = round(best["distance"] / 1000, 1)
    duration_hours = round(best["duration"] / 3600, 1)

    return {
        "available": True,
        "origin": origin,
        "destination": destination,
        "distance_km": distance_km,
        "duration_hours": duration_hours,
        "note": f"Approx. {distance_km} km, {duration_hours} hr by road (live route via OSRM).",
    }
