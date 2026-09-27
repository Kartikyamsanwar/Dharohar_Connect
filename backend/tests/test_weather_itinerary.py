from app.agents.itinerary_agent import _build_day
from app.services.weather_service import _build_planning_impact

SITE = {"name": "Hampi", "indoor": "Archaeological Museum"}
TRAVEL = {"available": True, "origin": "Pune", "distance_km": 533.1, "duration_hours": 6.5}
NO_TRAVEL = {"available": False}


def wx(**kw):
    base = {"date": "2026-10-01", "temp": 28, "temp_max": 28, "temp_min": 20, "rain_probability": 10, "thunderstorm": False,
            "windows": {"morning": 5, "afternoon": 5, "evening": 5}, "source": "forecast"}
    base.update(kw)
    return base


def test_only_wet_afternoon_moves_afternoon_indoors():
    w = wx(rain_probability=80, windows={"morning": 10, "afternoon": 85, "evening": 20})
    _, acts, note = _build_day(0, 3, SITE, w, NO_TRAVEL, {})
    assert "Guided exploration" in acts[0]
    assert "Indoor experience: Archaeological Museum" in acts[2]
    assert "Sunset viewpoint" in acts[3]
    assert "Afternoon rain risk" in note and "Morning" not in note


def test_heat_shifts_hours_and_afternoon():
    _, acts, note = _build_day(0, 3, SITE, wx(temp=39, temp_max=39), NO_TRAVEL, {})
    assert acts[0].startswith("06:30") and "Rest and indoor" in acts[2] and "Heat" in note


def test_thunderstorm_keeps_afternoon_indoors():
    _, acts, note = _build_day(0, 3, SITE, wx(thunderstorm=True), NO_TRAVEL, {})
    assert "Indoor experience" in acts[2] and "Thunderstorm" in note


def test_climatology_is_labelled_and_uses_day_probability():
    w = wx(rain_probability=70, windows={"morning": None, "afternoon": None, "evening": None}, source="climatology")
    _, acts, note = _build_day(0, 3, SITE, w, NO_TRAVEL, {})
    assert "Indoor experience" in acts[0] and "historical" in note


def test_arrival_and_departure_days():
    _, first, _ = _build_day(0, 3, SITE, wx(), TRAVEL, {})
    assert first[0].startswith("06:00 - Depart Pune") and first[1].startswith("15:30")
    _, last, note = _build_day(2, 3, SITE, wx(), TRAVEL, {})
    assert last[-1].startswith("Depart for Pune") and len(last) == 3 and "Departure day" in note


def test_planning_impact_messages():
    out = _build_planning_impact([wx(rain_probability=90), wx(date="2026-10-02", temp_max=40, temp=40)], historical_days=2)
    joined = " ".join(out)
    assert "Rain likely" in joined and "Very hot" in joined and "historical averages" in joined
    assert "favourable" in _build_planning_impact([wx()])[0]
