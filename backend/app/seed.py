"""Seed the database on first run. Hotel and ticket inventory is DEMO data (is_demo=True) that
stands in for a real provider API; groups and community posts come from the curated JSON files."""

from app.data_loader import HERITAGE, _load
from app.db import SessionLocal
from app.models import Comment, Group, Hotel, Post, TicketType

HERITAGE_CITY = {
    "hampi": "Hampi", "ajanta": "Aurangabad", "ellora": "Aurangabad", "konark": "Konark", "sanchi": "Sanchi",
    "khajuraho": "Khajuraho", "red-fort": "Delhi", "mahabalipuram": "Mahabalipuram", "taj-mahal": "Agra",
    "qutub-minar": "Delhi", "fatehpur-sikri": "Agra", "humayuns-tomb": "Delhi", "brihadeeswarar": "Thanjavur",
    "amber-fort": "Jaipur", "hawa-mahal": "Jaipur", "jantar-mantar-jaipur": "Jaipur", "rani-ki-vav": "Patan",
    "dholavira": "Dholavira", "elephanta-caves": "Mumbai", "cst-mumbai": "Mumbai", "charminar": "Hyderabad",
    "golden-temple": "Amritsar", "pattadakal": "Pattadakal", "nalanda": "Nalanda",
    "mahabodhi-temple": "Bodh Gaya", "mysore-palace": "Mysuru", "victoria-memorial": "Kolkata",
}

TIERS = [
    ("budget", "Guesthouse", 900, 3.8, 12, ["WiFi", "Fan/AC", "Breakfast"], "Simple, clean rooms close to the heritage precinct."),
    ("comfort", "Heritage Inn", 2400, 4.2, 20, ["WiFi", "AC", "Restaurant", "Guided-tour desk"], "Comfortable mid-range stay with local cuisine and travel desk."),
    ("premium", "Grand Residency", 5800, 4.6, 8, ["WiFi", "AC", "Pool", "Restaurant", "Airport transfer"], "Premium stay with curated heritage experiences."),
]

TICKETS = [
    ("indian", "Indian Citizen", 40, "Standard entry for Indian citizens (indicative price)."),
    ("foreign", "Foreign Tourist", 600, "Standard entry for foreign nationals (indicative price)."),
    ("guide", "Entry + Guided Tour", 300, "Add-on: certified guide for the visit (indicative price)."),
]
FREE_ENTRY = {"golden-temple"}


def _seed_inventory(db) -> None:
    if db.query(Hotel).count() == 0:
        cities: dict = {}
        for site in HERITAGE:
            city = HERITAGE_CITY.get(site["id"], site["name"])
            entry = cities.setdefault(city, {"state": site["state"], "near": []})
            entry["near"].append(site["name"])
        for city, info in cities.items():
            slug = city.lower().replace(" ", "-")
            for tier, label, price, rating, rooms, amenities, desc in TIERS:
                db.add(Hotel(
                    id=f"{slug}-{tier}", name=f"{city} {label}", city=city, state=info["state"], tier=tier,
                    price_per_night=price, rating=rating, amenities=amenities, near=info["near"],
                    description=desc, rooms_total=rooms, is_demo=True,
                ))
    if db.query(TicketType).count() == 0:
        for site in HERITAGE:
            for key, label, price, desc in TICKETS:
                p = 0 if site["id"] in FREE_ENTRY and key != "guide" else price
                db.add(TicketType(
                    id=f"{site['id']}-{key}", heritage_id=site["id"], site_name=site["name"], name=label,
                    price=p, description=desc, daily_capacity=1500, is_demo=True,
                ))


def _seed_community(db) -> None:
    if db.query(Group).count() == 0:
        for g in _load("groups.json"):
            db.add(Group(
                id=g["id"], name=g["name"], destination=g["destination"], dates=g["dates"],
                budget_min=g["budget_min"], budget_max=g["budget_max"], interests=g["interests"],
                base_members=g["members"], capacity=g["capacity"], organizer=g["organizer"],
                description=g.get("description", ""), verified=g.get("verified", False),
            ))
    if db.query(Post).count() == 0:
        posts = _load("community.json")
        for p in posts:
            db.add(Post(
                id=p["id"], title=p["title"], description=p["description"], author=p["author"],
                category=p["category"], location=p["location"], date=p["date"], likes=p.get("likes", 0),
                label=p.get("label", "community"), related_heritage=p.get("related_heritage", ""),
            ))
        db.flush()  # posts must exist before comments insert (FK is enforced on Postgres, not on SQLite)
        for p in posts:
            for c in p.get("comments", []):
                db.add(Comment(post_id=p["id"], author=c["author"], text=c["text"], date=c.get("date", p["date"])))


def seed() -> None:
    with SessionLocal() as db:
        _seed_inventory(db)
        _seed_community(db)
        db.commit()
