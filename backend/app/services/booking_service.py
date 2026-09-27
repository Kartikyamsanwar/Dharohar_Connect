"""Availability and booking rules for hotels and monument tickets.

Payments are SIMULATED (test mode): a booking is confirmed and marked 'simulated_paid'.
Wire a real gateway (e.g. Razorpay) here before taking real money."""

from datetime import date, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data_loader import HERITAGE
from app.models import Booking, Hotel, TicketType, User

MAX_NIGHTS = 30
MAX_ROOMS = 5
GUESTS_PER_ROOM = 3
MAX_TICKETS = 10
TICKET_ADVANCE_DAYS = 180
PAYMENT_NOTE = "Test mode - no real payment was processed."


def new_ref() -> str:
    return "DHR-" + uuid4().hex[:8].upper()


def parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise HTTPException(422, f"{label} must be a valid date (YYYY-MM-DD).")


def serialize(b: Booking) -> dict:
    return {
        "ref": b.ref, "kind": b.kind, "item_id": b.item_id, "item_name": b.item_name, "destination": b.destination,
        "start_date": b.start_date.isoformat(), "end_date": b.end_date.isoformat(), "quantity": b.quantity,
        "guests": b.guests, "total": b.total, "status": b.status, "payment_status": b.payment_status,
        "details": b.details, "created_at": b.created_at.isoformat() + "Z", "payment_note": PAYMENT_NOTE,
    }


def hotel_available_rooms(db: Session, hotel: Hotel, check_in: date, check_out: date) -> int:
    """Rooms free on EVERY night of the stay (max occupancy over the range)."""
    overlapping = (
        db.query(Booking)
        .filter(Booking.kind == "hotel", Booking.item_id == hotel.id, Booking.status == "confirmed",
                Booking.start_date < check_out, Booking.end_date > check_in)
        .all()
    )
    peak = 0
    night = check_in
    while night < check_out:
        peak = max(peak, sum(b.quantity for b in overlapping if b.start_date <= night < b.end_date))
        night += timedelta(days=1)
    return max(hotel.rooms_total - peak, 0)


def validate_stay(check_in_s: str, check_out_s: str, rooms: int, guests: int) -> tuple[date, date]:
    check_in, check_out = parse_date(check_in_s, "Check-in"), parse_date(check_out_s, "Check-out")
    if check_in < date.today():
        raise HTTPException(422, "Check-in cannot be in the past.")
    if check_out <= check_in:
        raise HTTPException(422, "Check-out must be after check-in.")
    if (check_out - check_in).days > MAX_NIGHTS:
        raise HTTPException(422, f"Stays are limited to {MAX_NIGHTS} nights.")
    if not 1 <= rooms <= MAX_ROOMS:
        raise HTTPException(422, f"Rooms must be between 1 and {MAX_ROOMS}.")
    if not 1 <= guests <= rooms * GUESTS_PER_ROOM:
        raise HTTPException(422, f"{rooms} room(s) hold at most {rooms * GUESTS_PER_ROOM} guests.")
    return check_in, check_out


def book_hotel(db: Session, user: User, hotel_id: str, check_in_s: str, check_out_s: str, rooms: int, guests: int) -> Booking:
    check_in, check_out = validate_stay(check_in_s, check_out_s, rooms, guests)
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).with_for_update().first()  # row lock on Postgres
    if not hotel:
        raise HTTPException(404, "Hotel not found.")
    free = hotel_available_rooms(db, hotel, check_in, check_out)
    if free < rooms:
        raise HTTPException(409, f"Only {free} room(s) left for those dates." if free else "Sold out for those dates.")
    nights = (check_out - check_in).days
    booking = Booking(
        ref=new_ref(), user_id=user.id, kind="hotel", item_id=hotel.id, item_name=hotel.name, destination=hotel.city,
        start_date=check_in, end_date=check_out, quantity=rooms, guests=guests,
        total=hotel.price_per_night * nights * rooms,
        details={"nights": nights, "price_per_night": hotel.price_per_night, "tier": hotel.tier, "guest_name": user.name},
    )
    db.add(booking)
    db.commit()
    return booking


def ticket_available(db: Session, ticket: TicketType, visit: date) -> int:
    used = sum(
        b.quantity for b in db.query(Booking).filter(
            Booking.kind == "ticket", Booking.item_id == ticket.id, Booking.status == "confirmed", Booking.start_date == visit
        )
    )
    return max(ticket.daily_capacity - used, 0)


def validate_visit(visit_s: str) -> date:
    visit = parse_date(visit_s, "Visit date")
    if visit < date.today():
        raise HTTPException(422, "Visit date cannot be in the past.")
    if visit > date.today() + timedelta(days=TICKET_ADVANCE_DAYS):
        raise HTTPException(422, f"Tickets can be booked up to {TICKET_ADVANCE_DAYS} days ahead.")
    return visit


def book_ticket(db: Session, user: User, ticket_id: str, visit_s: str, quantity: int) -> Booking:
    visit = validate_visit(visit_s)
    if not 1 <= quantity <= MAX_TICKETS:
        raise HTTPException(422, f"Quantity must be between 1 and {MAX_TICKETS}.")
    ticket = db.query(TicketType).filter(TicketType.id == ticket_id).with_for_update().first()
    if not ticket:
        raise HTTPException(404, "Ticket type not found.")
    left = ticket_available(db, ticket, visit)
    if left < quantity:
        raise HTTPException(409, f"Only {left} ticket(s) left for that day." if left else "Sold out for that day.")
    site = next((h for h in HERITAGE if h["id"] == ticket.heritage_id), {})
    booking = Booking(
        ref=new_ref(), user_id=user.id, kind="ticket", item_id=ticket.id, item_name=f"{ticket.site_name} - {ticket.name}",
        destination=site.get("state", ""), start_date=visit, end_date=visit, quantity=quantity, guests=quantity,
        total=ticket.price * quantity, details={"unit_price": ticket.price, "visitor_name": user.name, "site": ticket.site_name},
    )
    db.add(booking)
    db.commit()
    return booking


def cancel_booking(db: Session, user: User, ref: str) -> Booking:
    booking = db.query(Booking).filter(Booking.ref == ref, Booking.user_id == user.id).first()
    if not booking:
        raise HTTPException(404, "Booking not found.")
    if booking.status == "cancelled":
        raise HTTPException(409, "This booking is already cancelled.")
    limit = booking.start_date if booking.kind == "hotel" else booking.start_date + timedelta(days=1)
    if date.today() >= limit:
        raise HTTPException(409, "This booking has already started and can no longer be cancelled.")
    booking.status = "cancelled"
    booking.payment_status = "refunded_simulated"
    db.commit()
    return booking
