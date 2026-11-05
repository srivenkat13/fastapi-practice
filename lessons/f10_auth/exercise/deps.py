from typing import Annotated

from fastapi import Depends, Header, HTTPException, status  # noqa: F401
from fastapi.security import OAuth2PasswordBearer  # noqa: F401

from . import store
from .security import InvalidToken, decode_access_token  # noqa: F401

# TODO: oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(x_user_id: Annotated[str | None, Header()] = None) -> dict:
    """🐛 Trusts a client-supplied header! Anyone can send X-User-Id: 1 and become admin.

    TODO: take the bearer token (Depends(oauth2_scheme)), decode it with decode_access_token,
    load the user from store.USERS by int(claims["sub"]). Any failure -> 401 with
    headers={"WWW-Authenticate": "Bearer"}.
    """
    user = store.USERS.get(int(x_user_id or 0))
    if user is None:
        raise HTTPException(401, "Not authenticated")
    return user


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_role(*roles: str):
    """TODO: return a dependency that 403s unless the current user's role is in `roles`."""

    def checker():
        return None

    return checker
