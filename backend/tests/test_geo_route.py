import asyncio

import httpx

from app.services import travel_service
from app.services.geo import lookup
from app.services.weather_service import _friendly


def test_builtin_lookup_covers_cities_aliases_and_sites():
    assert lookup("Pune, Maharashtra")["name"] == "Pune"
    assert lookup("Bangalore")["name"] == "Bengaluru"
    assert lookup("Taj Mahal")["name"] == "Agra"
    assert lookup("Panaji")["state"] == "Goa"
    assert lookup("Dholavira") is not None and lookup("Nalanda") is not None
    assert lookup("Atlantis") is None


def test_route_falls_back_to_labelled_estimate_when_router_unreachable(monkeypatch):
    monkeypatch.setattr(travel_service, "OSRM_URL", "http://127.0.0.1:9/route")
    travel_service._routes.clear()
    r = asyncio.run(travel_service.get_route("Pune", "Hampi"))
    assert r["available"] and r["estimated"]
    assert 500 < r["distance_km"] < 620 and "estimated" in r["note"]


def test_rate_limit_error_is_explained_in_plain_words():
    resp = httpx.Response(429, request=httpx.Request("GET", "https://api.open-meteo.com"))
    msg = _friendly(httpx.HTTPStatusError("429", request=resp.request, response=resp))
    assert "rate-limiting" in msg and "try again" in msg
