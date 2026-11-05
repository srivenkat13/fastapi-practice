"""Password hashing and JWTs. Pure functions: no FastAPI imports."""
import os
from datetime import datetime, timedelta, timezone  # noqa: F401

import jwt  # noqa: F401  (PyJWT)
from pwdlib import PasswordHash  # noqa: F401

SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "dev-only-secret-change-me-in-production-0123456789")
ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=15)


class InvalidToken(Exception):
    pass


def hash_password(password: str) -> str:
    """Use pwdlib: PasswordHash.recommended().hash(password)  (Argon2id)."""
    return password  # 🐛 plaintext!


def verify_password(password: str, hashed: str) -> bool:
    return password == hashed  # 🐛


def create_access_token(subject: str, role: str, expires_delta: timedelta = ACCESS_TOKEN_TTL) -> str:
    """jwt.encode({"sub", "role", "iat", "exp"}, SECRET_KEY, algorithm=ALGORITHM)."""
    raise NotImplementedError


def decode_access_token(token: str) -> dict:
    """jwt.decode with a pinned algorithms=[ALGORITHM] list; require "exp" and "sub".
    Convert ANY jwt.PyJWTError into InvalidToken."""
    raise NotImplementedError
