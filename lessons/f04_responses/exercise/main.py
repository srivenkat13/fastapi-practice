from typing import Annotated, Generic, TypeVar  # noqa: F401

from fastapi import FastAPI, HTTPException, Query, Response, status  # noqa: F401
from pydantic import BaseModel, EmailStr, computed_field  # noqa: F401

app = FastAPI(title="F04 · Responses")
T = TypeVar("T")


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str


class UserInDB(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    password_hash: str
    internal_notes: str = ""


# TODO: class UserPublic(BaseModel): id, email, first_name, last_name + computed display_name ("Ada Lovelace")

# TODO: class Page(BaseModel, Generic[T]): items: list[T], total, limit, offset


def fake_hash(password: str) -> str:
    return "hashed$" + password[::-1]


USERS: dict[int, UserInDB] = {}


@app.post("/users")  # TODO: 201 + Location header + response model
def create_user(user: UserCreate):
    new_id = max(USERS, default=0) + 1
    data = user.model_dump(exclude={"password"})
    USERS[new_id] = UserInDB(id=new_id, password_hash=fake_hash(user.password), **data)
    return USERS[new_id]


@app.get("/users/{user_id}")  # TODO: response model
def get_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(404, "User not found")
    return USERS[user_id]


@app.get("/users")  # TODO: Page[UserPublic] with limit (1..100, default 20) & offset (>= 0, default 0)
def list_users():
    return list(USERS.values())


# TODO: DELETE /users/{user_id} -> 204 with no body; 404 if missing
