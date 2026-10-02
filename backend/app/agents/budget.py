"""Rough per-person trip cost estimate. Rates are fixed planning assumptions, not live prices."""

import math

ROAD_RATE_PER_KM = 7          # shared car: fuel + tolls, round trip, split across travellers
ROOM_PER_NIGHT = 1200         # one double room
FOOD_PER_DAY = 500            # per person
LOCAL_PER_DAY = 300           # per person: entry tickets + local transport


def estimate_budget(req: dict, travel: dict, room_rate: int | None = None, room_label: str = "") -> dict:
    room_rate = room_rate or ROOM_PER_NIGHT
    days = max(int(req.get("days", 1)), 1)
    travelers = max(int(req.get("travelers", 1) or 1), 1)
    budget = float(req.get("budget", 0) or 0)
    nights = max(days - 1, 0)

    if travel.get("available"):
        transport_total = travel["distance_km"] * 2 * ROAD_RATE_PER_KM
        transport_basis = f"{travel['distance_km']} km x 2 (round trip) x Rs {ROAD_RATE_PER_KM}/km, shared by {travelers}"
    else:
        transport_total = 0
        transport_basis = "Route unavailable - transport not included"

    rooms = math.ceil(travelers / 2)
    breakdown = {
        "transport": round(transport_total / travelers),
        "stay": round(nights * room_rate * rooms / travelers),
        "food": FOOD_PER_DAY * days,
        "local": LOCAL_PER_DAY * days,
    }
    total = sum(breakdown.values())

    return {
        "per_person_total": total,
        "breakdown": breakdown,
        "budget_per_person": round(budget),
        "within_budget": total <= budget if budget else None,
        "difference": round(budget - total) if budget else None,
        "assumptions": [
            f"Transport: {transport_basis}",
            f"Stay: {room_label + ' at ' if room_label else ''}Rs {room_rate}/room/night, {rooms} room(s), {nights} night(s)",
            f"Food: Rs {FOOD_PER_DAY}/person/day",
            f"Entry tickets and local transport: Rs {LOCAL_PER_DAY}/person/day",
            "Planning estimate only; actual prices vary by season and provider.",
        ],
    }
