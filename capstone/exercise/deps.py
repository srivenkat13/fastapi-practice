from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_session
from .models import User
from .security import InvalidToken, decode_access_token

DB = Annotated[Session, Depends(get_session)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    error = HTTPException(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = decode_access_token(token)
    except InvalidToken:
        raise error
    user = db.get(User, user_id)
    if user is None:
        raise error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
