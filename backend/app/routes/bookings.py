from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.data_loader import HERITAGE, SITE_CITY
from app.db import get_db
from app.models import Booking, Hotel, SavedTrip, TicketType, User
from app.security import current_user
from app.services import booking_service as svc

router = APIRouter(tags=["bookings"])


def _matching_cities(query: str) -> set[str]:
    """Resolve a free-text destination (site, city or state) to hotel cities."""
    q = query.lower().strip()
    cities = set()
    for site in HERITAGE:
        if q and (q in site["name"].lower() or q in site["state"].lower() or q in SITE_CITY.get(site["id"], "").lower()):
            cities.add(SITE_CITY.get(site["id"], site["name"]))
    return cities


@router.get("/hotels")
def search_hotels(
    destination: str = "", check_in: str = "", check_out: str = "", guests: int = 1, rooms: int = 1,
    db: Session = Depends(get_db),
):
    hotels = db.query(Hotel).all()
    if destination.strip():
        cities = _matching_cities(destination)
        q = destination.lower().strip()
        hotels = [h for h in hotels if h.city in cities or q in h.city.lower()]
    dated = bool(check_in and check_out)
    nights = 0
    if dated:
        ci, co = svc.validate_stay(check_in, check_out, max(rooms, 1), max(guests, 1))
        nights = (co - ci).days
    out = []
    for h in hotels:
        item = {
            "id": h.id, "name": h.name, "city": h.city, "state": h.state, "tier": h.tier, "rating": h.rating,
            "price_per_night": h.price_per_night, "amenities": h.amenities, "near": h.near,
            "description": h.description, "is_demo": h.is_demo,
        }
        if dated:
            free = svc.hotel_available_rooms(db, h, ci, co)
            item.update(available_rooms=free, nights=nights, total_price=h.price_per_night * nights * rooms, bookable=free >= rooms)
        out.append(item)
    out.sort(key=lambda x: x["price_per_night"])
    return {"hotels": out, "inventory_note": "Demo inventory - stands in for a live hotel-provider API. Prices exclude taxes."}


class HotelBookingRequest(BaseModel):
    hotel_id: str
    check_in: str
    check_out: str
    rooms: int = Field(default=1, ge=1)
    guests: int = Field(default=1, ge=1)


@router.post("/bookings/hotel")
def book_hotel(req: HotelBookingRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.serialize(svc.book_hotel(db, user, req.hotel_id, req.check_in, req.check_out, req.rooms, req.guests))


@router.get("/tickets")
def list_tickets(destination: str = "", visit_date: str = "", db: Session = Depends(get_db)):
    visit = svc.validate_visit(visit_date) if visit_date else None
    q = destination.lower().strip()
    sites = [s for s in HERITAGE if not q or q in s["name"].lower() or q in s["state"].lower()
             or q == SITE_CITY.get(s["id"], "").lower()]
    tickets = db.query(TicketType).all()
    result = []
    for site in sites:
        types = []
        for t in (x for x in tickets if x.heritage_id == site["id"]):
            row = {"id": t.id, "name": t.name, "price": t.price, "description": t.description}
            if visit:
                row["available"] = svc.ticket_available(db, t, visit)
            types.append(row)
        result.append({"heritage_id": site["id"], "site": site["name"], "state": site["state"], "best_time": site.get("best_time", ""), "tickets": types})
    return {"sites": result, "inventory_note": "Indicative prices; demo inventory. Confirm on the official ASI/state ticketing portal."}


class TicketBookingRequest(BaseModel):
    ticket_id: str
    visit_date: str
    quantity: int = Field(default=1, ge=1)


@router.post("/bookings/ticket")
def book_ticket(req: TicketBookingRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.serialize(svc.book_ticket(db, user, req.ticket_id, req.visit_date, req.quantity))


@router.get("/bookings")
def my_bookings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Booking).filter(Booking.user_id == user.id).order_by(Booking.created_at.desc()).all()
    return {"bookings": [svc.serialize(b) for b in rows]}


@router.post("/bookings/{ref}/cancel")
def cancel(ref: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.serialize(svc.cancel_booking(db, user, ref))


class SaveTripRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    destination: str
    start_date: str
    days: int
    payload: dict


@router.post("/trips")
def save_trip(req: SaveTripRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    trip = SavedTrip(user_id=user.id, title=req.title, destination=req.destination, start_date=req.start_date, days=req.days, payload=req.payload)
    db.add(trip)
    db.commit()
    return {"id": trip.id, "title": trip.title}


@router.get("/trips")
def my_trips(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(SavedTrip).filter(SavedTrip.user_id == user.id).order_by(SavedTrip.created_at.desc()).all()
    return {"trips": [{"id": t.id, "title": t.title, "destination": t.destination, "start_date": t.start_date, "days": t.days,
                       "payload": t.payload, "created_at": t.created_at.isoformat() + "Z"} for t in rows]}


@router.delete("/trips/{trip_id}")
def delete_trip(trip_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    trip = db.query(SavedTrip).filter(SavedTrip.id == trip_id, SavedTrip.user_id == user.id).first()
    if not trip:
        raise HTTPException(404, "Trip not found.")
    db.delete(trip)
    db.commit()
    return {"deleted": trip_id}
