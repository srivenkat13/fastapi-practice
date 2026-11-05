"""Hashing + JWT (you built this in F10)."""
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

SECRET_KEY = os.environ.get("CAPSTONE_SECRET_KEY", "capstone-dev-secret-change-me-0123456789abcdef")
ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


class InvalidToken(Exception):
    pass


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: int, ttl: timedelta = timedelta(minutes=30)) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": now + ttl}, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        return int(jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise InvalidToken() from exc
