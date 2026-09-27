from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), default="")
    password_hash: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Hotel(Base):
    __tablename__ = "hotels"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100))
    tier: Mapped[str] = mapped_column(String(30))
    price_per_night: Mapped[int] = mapped_column(Integer)
    rating: Mapped[float] = mapped_column(Float)
    amenities: Mapped[list] = mapped_column(JSON, default=list)
    near: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    rooms_total: Mapped[int] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class TicketType(Base):
    __tablename__ = "ticket_types"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    heritage_id: Mapped[str] = mapped_column(String(80), index=True)
    site_name: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(300), default="")
    daily_capacity: Mapped[int] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    ref: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(10))
    item_id: Mapped[str] = mapped_column(String(80), index=True)
    item_name: Mapped[str] = mapped_column(String(250))
    destination: Mapped[str] = mapped_column(String(120))
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer)
    guests: Mapped[int] = mapped_column(Integer, default=1)
    total: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="confirmed", index=True)
    payment_status: Mapped[str] = mapped_column(String(30), default="simulated_paid")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SavedTrip(Base):
    __tablename__ = "saved_trips"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    destination: Mapped[str] = mapped_column(String(120))
    start_date: Mapped[str] = mapped_column(String(12))
    days: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Group(Base):
    __tablename__ = "groups"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    destination: Mapped[str] = mapped_column(String(120), index=True)
    dates: Mapped[str] = mapped_column(String(120))
    budget_min: Mapped[float] = mapped_column(Float)
    budget_max: Mapped[float] = mapped_column(Float)
    interests: Mapped[str] = mapped_column(String(200))
    base_members: Mapped[int] = mapped_column(Integer, default=1)
    capacity: Mapped[int] = mapped_column(Integer, default=6)
    organizer: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60), index=True)
    location: Mapped[str] = mapped_column(String(120))
    date: Mapped[str] = mapped_column(String(12), index=True)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[str] = mapped_column(String(20), default="community")
    related_heritage: Mapped[str] = mapped_column(String(120), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"), index=True)
    author: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String(12))
