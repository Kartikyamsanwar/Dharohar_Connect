"""Recommendation Agent — synthesizes heritage, weather and travel inputs."""

from app.agents.budget import estimate_budget
from app.services.llm_service import generate_response, is_llm_available

RECOMMENDATION_PROMPT = """You are the DHAROHAR Recommendation Agent.
Given heritage sites, weather forecast, travel info and a budget estimate, produce 3 concise bullet
recommendations (max 25 words each) for a heritage trip. Focus on timing, site priorities,
weather-aware suggestions and whether the plan fits the budget.
Use only provided data. Do not invent weather, prices or facts."""


def build_recommendations(state: dict) -> dict:
    req = state.get("request", {})
    heritage = state.get("heritage", [])
    weather = state.get("weather", {})
    travel = state.get("travel", {})

    site_names = [h.get("name", "") for h in heritage]
    weather_note = (
        "Live weather connected"
        if weather.get("available")
        else "Live weather unavailable"
    )
    impacts = weather.get("planning_impact", [])

    budget = estimate_budget(req, travel)
    base = {
        "highlights": site_names or [req.get("destination", "Heritage destination")],
        "weather_status": weather_note,
        "planning_notes": impacts,
        "travel_note": travel.get("note", ""),
        "budget": budget,
    }

    if is_llm_available() and heritage:
        context = (
            f"Destination: {req.get('destination')}\n"
            f"Days: {req.get('days')}\n"
            f"Interests: {req.get('interests')}\n"
            f"Heritage: {[h.get('name') for h in heritage]}\n"
            f"Weather: {weather.get('forecast', [])}\n"
            f"Impacts: {impacts}\n"
            f"Travel: {travel.get('note', 'Route information unavailable')}\n"
            f"Budget per person: Rs {budget['budget_per_person']}; estimated cost Rs {budget['per_person_total']} "
            f"(breakdown {budget['breakdown']})"
        )
        llm = generate_response(
            "Provide trip recommendations.",
            system_prompt=RECOMMENDATION_PROMPT,
            context=context,
            max_tokens=900,
        )
        if llm["mode"] == "groq":
            base["summary"] = llm["text"]
            return base

    notes = []
    if site_names:
        notes.append(f"Prioritize visits to {', '.join(site_names)}.")
    notes.extend(impacts)
    if req.get("interests"):
        notes.append(f"Tailor experiences to interests: {req['interests']}.")
    base["summary"] = " ".join(notes)
    return base
