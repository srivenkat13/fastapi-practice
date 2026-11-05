from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from ..deps import DB, CurrentUser
from ..models import User
from ..schemas import Token, UserCreate, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: DB):
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email already registered")
    user = User(email=data.email.lower(), name=data.name, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return user


@router.post("/auth/token", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(user.id))


@router.get("/users/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
