import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _load(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


HERITAGE = _load("heritage.json")
CULTURE = _load("culture.json")
HERITAGE_BY_ID = {s["id"]: s for s in HERITAGE}

# Nearest city used for weather, routing and hotel search.
SITE_CITY = {
    "hampi": "Hampi", "ajanta": "Aurangabad", "ellora": "Aurangabad", "konark": "Konark", "sanchi": "Sanchi",
    "khajuraho": "Khajuraho", "red-fort": "Delhi", "mahabalipuram": "Mahabalipuram", "taj-mahal": "Agra",
    "qutub-minar": "Delhi", "fatehpur-sikri": "Agra", "humayuns-tomb": "Delhi", "brihadeeswarar": "Thanjavur",
    "amber-fort": "Jaipur", "hawa-mahal": "Jaipur", "jantar-mantar-jaipur": "Jaipur", "rani-ki-vav": "Patan",
    "dholavira": "Dholavira", "elephanta-caves": "Mumbai", "cst-mumbai": "Mumbai", "charminar": "Hyderabad",
    "golden-temple": "Amritsar", "pattadakal": "Pattadakal", "nalanda": "Nalanda",
    "mahabodhi-temple": "Bodh Gaya", "mysore-palace": "Mysuru", "victoria-memorial": "Kolkata",
}

ALIASES = {
    "kailasa": "ellora", "kailash": "ellora", "verul": "ellora", "virupaksha": "hampi", "vijayanagara": "hampi",
    "qutb": "qutub-minar", "kutub": "qutub-minar", "amer": "amber-fort", "harmandir": "golden-temple",
    "darbar sahib": "golden-temple", "bodh gaya": "mahabodhi-temple", "bodhgaya": "mahabodhi-temple",
    "mamallapuram": "mahabalipuram", "shore temple": "mahabalipuram", "tanjore": "brihadeeswarar",
    "big temple": "brihadeeswarar", "rajarajeswaram": "brihadeeswarar", "victoria terminus": "cst-mumbai",
    "cst": "cst-mumbai", "buland darwaza": "fatehpur-sikri", "sun temple": "konark", "black pagoda": "konark",
    "trimurti": "elephanta-caves", "stepwell": "rani-ki-vav", "harappan": "dholavira", "indus valley": "dholavira",
    "lal qila": "red-fort", "humayun": "humayuns-tomb", "mysore": "mysore-palace", "mysuru": "mysore-palace",
    "pink city": "hawa-mahal", "observatory": "jantar-mantar-jaipur",
}

_STOP = {
    "what", "whats", "why", "how", "when", "where", "which", "who", "whom", "is", "are", "was", "were", "the", "a",
    "an", "of", "in", "on", "at", "to", "for", "from", "about", "tell", "me", "please", "can", "could", "you", "give",
    "show", "and", "or", "with", "its", "it", "this", "that", "there", "their", "they", "these", "those", "some",
    "any", "more", "much", "many", "very", "india", "indian", "heritage", "site", "sites", "place", "places", "visit",
    "visiting", "trip", "plan", "weather", "cost", "budget", "best", "time", "should", "would", "will", "do", "does",
    "did", "know", "explain", "describe", "like", "get", "go", "going", "near", "nearby", "my", "our", "we", "i",
}


# Words shared by many site names; matching one says little about which site is meant.
_GENERIC = {"temple", "fort", "caves", "cave", "group", "monuments", "palace", "tomb", "stupa", "memorial", "mahal"}


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if len(w) > 2 and w not in _STOP]


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


def _score(site: dict, q: str, words: set[str]) -> float:
    name = site["name"].lower()
    score = 0.0
    if name in q or name.split(" (")[0].split(",")[0] in q:
        score += 10
    score += sum(8 for alias, sid in ALIASES.items() if sid == site["id"] and re.search(rf"\b{re.escape(alias)}\b", q))
    city = SITE_CITY.get(site["id"], "").lower()
    if city and re.search(rf"\b{re.escape(city)}\b", q):
        score += 6
    if site["state"].lower() in q:
        score += 3
    name_words = set(_words(site["name"]))
    cat_words = set(_words(site["category"]))
    text_words = set(_words(site["description"] + " " + site["significance"]))
    hits = words & name_words
    score += 3 * len(hits - _GENERIC) + 0.5 * len(hits & _GENERIC)
    score += len(words & cat_words) + 0.5 * len(words & text_words)
    return score


def retrieve_heritage_knowledge(message: str, limit: int = 4) -> tuple[list, list]:
    """Keyword-scored retrieval over the curated records; returns (sites, source labels)."""
    q = message.lower()
    words = set(_words(message))
    scored = sorted(((_score(s, q, words), s) for s in HERITAGE), key=lambda x: x[0], reverse=True)
    top = scored[0][0] if scored else 0
    matches = [s for score, s in scored if score >= max(1.5, 0.4 * top)][:limit]
    sources = [src for m in matches for src in m.get("sources", [])]
    return matches, list(dict.fromkeys(sources))


def resolve_site(text: str) -> dict | None:
    """Best single site for a free-text place name, or None if nothing matches clearly."""
    if not text:
        return None
    if text in HERITAGE_BY_ID:
        return HERITAGE_BY_ID[text]
    q = text.lower().strip()
    if list(SITE_CITY.values()).count(text.strip().title()) > 1:
        return None  # a city with several sites (e.g. "Jaipur") is not one specific site
    scored = sorted(((_score(s, q, set(_words(text))), s) for s in HERITAGE), key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] >= 3 else None


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
