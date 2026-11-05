"""An in-memory user store (stands in for a users table)."""
from itertools import count

USERS: dict[int, dict] = {}
_ids = count(1)


def add_user(email: str, password_hash: str, role: str = "user") -> dict:
    user = {"id": next(_ids), "email": email.lower(), "password_hash": password_hash, "role": role}
    USERS[user["id"]] = user
    return user


def by_email(email: str) -> dict | None:
    return next((u for u in USERS.values() if u["email"] == email.lower()), None)


def reset(admin_hash: str) -> None:
    global _ids
    USERS.clear()
    _ids = count(1)
    add_user("admin@example.com", admin_hash, role="admin")
