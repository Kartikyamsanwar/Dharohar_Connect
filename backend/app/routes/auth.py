import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import create_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=128)
    phone: str = ""

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


def _public(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "phone": user.phone}


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = User(name=req.name.strip(), email=req.email, phone=req.phone.strip(), password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    return {"token": create_token(user.id), "user": _public(user)}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password.")
    return {"token": create_token(user.id), "user": _public(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _public(user)
