import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import JWT_EXPIRE_HOURS, JWT_SECRET
from app.db import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=False)
_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, digest = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(check.hex(), digest)
    except (ValueError, TypeError):
        return False


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": exp}, JWT_SECRET, algorithm="HS256")


def _user_from_credentials(creds: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if not creds:
        return None
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        return db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)) -> User:
    user = _user_from_credentials(creds, db)
    if not user:
        raise HTTPException(401, "Please log in to continue.")
    return user


def optional_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)) -> User | None:
    return _user_from_credentials(creds, db)
