import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _load(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


HERITAGE = _load("heritage.json")
CULTURE = _load("culture.json")


def find_heritage(name: str):
    q = name.lower().strip()
    exact = next((x for x in HERITAGE if x["name"].lower() == q), None)
    if exact:
        return exact
    return next(
        (x for x in HERITAGE if q in x["name"].lower() or q in x["state"].lower()),
        None,
    )


def search_heritage(query: str) -> list:
    if not query.strip():
        return HERITAGE
    ql = query.lower()
    return [
        x
        for x in HERITAGE
        if ql in (x["name"] + " " + x["state"] + " " + x["category"] + " " + x["description"]).lower()
    ]


def retrieve_heritage_knowledge(message: str) -> tuple[list, list]:
    """Return matching heritage records and their source labels."""
    q = message.lower()
    matches = []
    for site in HERITAGE:
        haystack = f"{site['name']} {site['state']} {site['category']} {site['description']} {site['significance']}".lower()
        if site["name"].lower() in q or any(word in haystack for word in q.split() if len(word) > 3):
            matches.append(site)
    sources = []
    for m in matches[:3]:
        sources.extend(m.get("sources", []))
    return matches[:3], list(dict.fromkeys(sources))


def _tokens(text: str) -> set:
    stop = {"and", "plus", "the", "with"}
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 2 and t not in stop}


def rank_groups(groups: list, destination: str = "", interests: str = "", budget: str = "") -> list:
    """Rank groups by compatibility: destination (required if given), budget fit and interest overlap."""
    try:
        b = float(budget) if budget else None
    except ValueError:
        b = None
    wanted = _tokens(interests)

    ranked = []
    for g in groups:
        earned, possible = 0.0, 0.0
        if destination:
            if destination.lower() not in g.get("destination", "").lower():
                continue
            earned += 40
            possible += 40
        if b is not None:
            possible += 30
            if g.get("budget_min", 0) <= b <= g.get("budget_max", 10**9):
                earned += 30
        if wanted:
            possible += 30
            theirs = _tokens(g.get("interests", ""))
            if theirs:
                earned += 30 * len(wanted & theirs) / len(wanted | theirs)
        score = round(100 * earned / possible) if possible else None
        ranked.append({**g, "match_score": score})

    if any([destination, b is not None, wanted]):
        ranked.sort(key=lambda x: x["match_score"] or 0, reverse=True)
    return ranked


def filter_culture(category: str = "", region: str = "") -> list:
    items = CULTURE
    if category:
        items = [c for c in items if c.get("category", "").lower() == category.lower()]
    if region:
        r = region.lower()
        items = [c for c in items if r in c.get("region", "").lower()]
    return items
