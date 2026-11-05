"""Password hashing and JWTs. Pure functions: no FastAPI imports, easy to unit test."""
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "dev-only-secret-change-me-in-production-0123456789")
ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=15)

password_hash = PasswordHash.recommended()  # Argon2id, the current OWASP recommendation


class InvalidToken(Exception):
    pass


def hash_password(password: str) -> str:
    return password_hash.hash(password)  # salted; same password → different hash each time


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)  # constant-time comparison


def create_access_token(subject: str, role: str, expires_delta: timedelta = ACCESS_TOKEN_TTL) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": subject, "role": role, "iat": now, "exp": now + expires_delta}
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        # algorithms=[...] is a pinned allow-list: rejects "alg": "none" and algorithm-confusion attacks.
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError as exc:  # expired, bad signature, malformed, missing claims...
        raise InvalidToken(str(exc)) from exc
