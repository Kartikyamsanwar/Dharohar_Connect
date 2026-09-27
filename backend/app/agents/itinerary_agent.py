"""Itinerary Agent - date-matched, slot-level weather-adaptive day plans with optional Groq tips."""

from datetime import date, timedelta

from app.services.llm_service import generate_response, is_llm_available
from app.services.weather_service import HEAT_THRESHOLD_C, RAIN_THRESHOLD_PCT

ITINERARY_PROMPT = """You are the DHAROHAR Itinerary Agent.
Give 2 short practical timing tips (max 30 words each) for this heritage itinerary using ONLY the
provided heritage and weather data. Do not invent sites, prices or weather."""

THEMES = [
    "Iconic core monuments",
    "Museums, crafts and living culture",
    "Hidden corners and golden-hour photography",
]


def _start_date(req: dict) -> date:
    try:
        return date.fromisoformat(req.get("date", ""))
    except (TypeError, ValueError):
        return date.today()


def _slots(site: dict, theme_idx: int) -> dict:
    """Return {slot: (text, outdoor)} for morning / afternoon / evening."""
    name = site["name"]
    indoor = site.get("indoor", "local museum / interpretation centre")
    if theme_idx == 0:
        return {
            "morning": (f"Guided exploration of the main monuments at {name}", True),
            "afternoon": (f"Study the architecture and inscriptions of {name}", True),
            "evening": (f"Sunset viewpoint around {name}", True),
        }
    if theme_idx == 1:
        return {
            "morning": (f"Museum visit: {indoor}", False),
            "afternoon": ("Meet local artisans; try regional food heritage", False),
            "evening": ("Evening cultural walk through the local market area", True),
        }
    return {
        "morning": (f"Sunrise photography at {name} (quieter, cooler hours)", True),
        "afternoon": (f"Explore lesser-visited corners of {name}", True),
        "evening": ("Golden-hour photo walk and journaling", True),
    }


def _wet(wx: dict | None, slot: str) -> bool:
    if not wx:
        return False
    p = (wx.get("windows") or {}).get(slot)
    if p is None:
        p = wx.get("rain_probability", 0)
    return p >= RAIN_THRESHOLD_PCT


def _build_day(i: int, days: int, site: dict, wx: dict | None, travel: dict, req: dict):
    indoor = site.get("indoor", "local museum / interpretation centre")
    theme_idx = i % len(THEMES)
    slots = _slots(site, theme_idx)
    hot = bool(wx and wx.get("temp_max", wx.get("temp", 0)) >= HEAT_THRESHOLD_C)
    stormy = bool(wx and wx.get("thunderstorm"))
    activities: list[str] = []
    notes: list[str] = []

    arrival = i == 0 and travel.get("available")
    late_start = bool(arrival and travel.get("duration_hours", 0) >= 5)
    if arrival:
        activities.append(
            f"06:00 - Depart {travel['origin']} ({travel['distance_km']} km, about {travel['duration_hours']} hr by road)"
        )
        notes.append("Arrival day: heritage visits start after the drive.")

    times = {"morning": "06:30" if hot else "08:00", "afternoon": "15:00", "evening": "17:30" if hot else "18:00"}

    def pick(slot: str):
        text, outdoor = slots[slot]
        wet = _wet(wx, slot)
        if outdoor and wet:
            pct = (wx.get("windows") or {}).get(slot) or wx.get("rain_probability")
            notes.append(f"{slot.capitalize()} rain risk ({pct}%): moved indoors.")
            return f"Indoor experience: {indoor}" if slot != "evening" else "Indoor cultural evening: heritage talk or performance", False
        if outdoor and stormy and slot == "afternoon":
            notes.append("Thunderstorm risk: afternoon kept indoors.")
            return f"Indoor experience: {indoor}", False
        if outdoor and hot and slot == "afternoon":
            notes.append(f"Heat ({wx['temp_max']} C): afternoon kept indoors.")
            return f"Rest and indoor interpretation: {indoor}", False
        return text, outdoor

    if late_start:
        text, _ = pick("afternoon")
        activities.append(f"15:30 - Check in, then light visit: {text}")
        text, _ = pick("evening")
        activities.append(f"{times['evening']} - {text}")
    else:
        text, _ = pick("morning")
        activities.append(f"{times['morning']} - {text}")
        activities.append("12:30 - Local lunch and rest")
        text, _ = pick("afternoon")
        activities.append(f"{times['afternoon']} - {text}")
        text, _ = pick("evening")
        activities.append(f"{times['evening']} - {text}")

    if i == days - 1 and days > 1 and travel.get("available"):
        activities = activities[:2] + [f"Depart for {travel['origin']} after lunch (about {travel['duration_hours']} hr drive)"]
        notes.append("Departure day: keep the evening free for the return drive.")

    if not wx:
        notes.append("Standard schedule (no weather data for this date).")
    elif wx.get("source") == "climatology":
        notes.append("Based on historical averages, not a live forecast.")
    elif not any("moved" in n or "kept indoors" in n for n in notes):
        notes.append("Outdoor-friendly conditions.")

    return THEMES[theme_idx], activities, " ".join(notes)


def build_itinerary(state: dict) -> list:
    req = state.get("request", {})
    heritage = state.get("heritage", [])
    weather = state.get("weather", {})
    travel = state.get("travel", {})
    days = max(int(req.get("days", 1)), 1)
    forecast = weather.get("forecast", []) if weather.get("available") else []
    by_date = {f["date"]: f for f in forecast}
    start = _start_date(req)

    sites = heritage or [
        {"name": req.get("destination", "Heritage destination"), "significance": "Explore the local heritage landscape.", "indoor": "local museum"}
    ]
    site = sites[0]

    result = []
    for i in range(days):
        day_date = (start + timedelta(days=i)).isoformat()
        wx = by_date.get(day_date)
        theme, activities, note = _build_day(i, days, site, wx, travel, req)
        result.append({"day": i + 1, "date": day_date, "theme": theme, "weather": wx, "activities": activities, "note": note})

    if is_llm_available() and heritage:
        context = f"Heritage: {[h.get('name') for h in heritage]}\nForecast: {forecast}\nDays: {days}"
        llm = generate_response("Give timing tips for this itinerary.", system_prompt=ITINERARY_PROMPT, context=context, max_tokens=600)
        if llm["mode"] == "groq" and llm["text"] and result:
            result[0]["agent_note"] = llm["text"]

    return result
