from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from . import store
from .security import InvalidToken, decode_access_token

# Reads "Authorization: Bearer <token>" (401 if missing) and wires up /docs' Authorize button.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

CREDENTIALS_ERROR = HTTPException(
    status.HTTP_401_UNAUTHORIZED, "Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    try:
        claims = decode_access_token(token)
    except InvalidToken:
        raise CREDENTIALS_ERROR
    user = store.USERS.get(int(claims["sub"]))
    if user is None:  # deleted after the token was issued
        raise CREDENTIALS_ERROR
    return user


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_role(*roles: str):
    def checker(user: CurrentUser) -> dict:
        if user["role"] not in roles:  # read the role from the DB user, not only the token claim
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
        return user

    return checker
