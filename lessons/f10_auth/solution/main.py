from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from . import store
from .deps import CurrentUser, require_role
from .security import create_access_token, hash_password, verify_password

app = FastAPI(title="F10 · Auth")
store.reset(hash_password("adminpass123"))


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn):
    if store.by_email(data.email):
        raise HTTPException(409, "Email already registered")
    return store.add_user(data.email, hash_password(data.password))


@app.post("/auth/token", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """OAuth2 password flow: form fields `username` (our email) + `password`. Powers the Authorize button in /docs."""
    user = store.by_email(form.username)
    # Same error for "no such user" and "wrong password": don't reveal which emails exist.
    if user is None or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"}
        )
    return Token(access_token=create_access_token(str(user["id"]), user["role"]))


@app.get("/users/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@app.get("/admin/users", response_model=list[UserOut], dependencies=[Depends(require_role("admin"))])
def all_users():
    return list(store.USERS.values())
