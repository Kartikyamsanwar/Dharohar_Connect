from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data_loader import rank_groups
from app.db import get_db
from app.models import Group, GroupMember, User
from app.security import current_user, optional_user

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    destination: str = Field(min_length=2, max_length=120)
    dates: str = Field(min_length=2, max_length=120)
    budget_min: float = Field(ge=0)
    budget_max: float = Field(ge=0)
    interests: str = ""
    capacity: int = Field(default=6, ge=2, le=50)
    description: str = ""


def _member_ids(db: Session, group_id: str) -> list[int]:
    return [m.user_id for m in db.query(GroupMember).filter(GroupMember.group_id == group_id).all()]


def _to_dict(db: Session, g: Group, user: User | None = None) -> dict:
    ids = _member_ids(db, g.id)
    return {
        "id": g.id, "name": g.name, "destination": g.destination, "dates": g.dates,
        "budget_min": g.budget_min, "budget_max": g.budget_max,
        "budget_label": f"₹{int(g.budget_min):,}–₹{int(g.budget_max):,}", "interests": g.interests,
        "members": g.base_members + len(ids), "capacity": g.capacity, "organizer": g.organizer,
        "description": g.description, "verified": g.verified, "joined": bool(user and user.id in ids),
    }


@router.get("")
def list_groups(destination: str = "", interests: str = "", budget: str = "", db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    groups = [_to_dict(db, g, user) for g in db.query(Group).all()]
    return {"groups": rank_groups(groups, destination, interests, budget), "demo": False}


@router.get("/{group_id}")
def group_detail(group_id: str, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(404, "Group not found")
    return _to_dict(db, g, user)


@router.post("")
def create_group(req: GroupCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if req.budget_max < req.budget_min:
        raise HTTPException(422, "Maximum budget must be at least the minimum budget.")
    g = Group(
        id=f"g-{uuid4().hex[:8]}", name=req.name, destination=req.destination, dates=req.dates,
        budget_min=req.budget_min, budget_max=req.budget_max, interests=req.interests, base_members=0,
        capacity=req.capacity, organizer=user.name, description=req.description, verified=False, created_by=user.id,
    )
    db.add(g)
    db.flush()  # group must exist before the membership row (FK is enforced on Postgres, not on SQLite)
    db.add(GroupMember(group_id=g.id, user_id=user.id))
    db.commit()
    return _to_dict(db, g, user)


@router.post("/{group_id}/join")
def join_group(group_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    g = db.query(Group).filter(Group.id == group_id).with_for_update().first()
    if not g:
        raise HTTPException(404, "Group not found")
    ids = _member_ids(db, g.id)
    if user.id in ids:
        raise HTTPException(409, "You have already joined this group.")
    if g.base_members + len(ids) >= g.capacity:
        raise HTTPException(400, "Group is full")
    db.add(GroupMember(group_id=g.id, user_id=user.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "You have already joined this group.")
    return {"message": "You joined the group.", "group": _to_dict(db, g, user)}


@router.post("/{group_id}/leave")
def leave_group(group_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    m = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == user.id).first()
    if not m:
        raise HTTPException(404, "You are not a member of this group.")
    db.delete(m)
    db.commit()
    return {"message": "You left the group.", "group": _to_dict(db, db.get(Group, group_id), user)}
