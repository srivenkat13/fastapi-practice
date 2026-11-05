from typing import Annotated, Generic, TypeVar

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, EmailStr, computed_field

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


class UserPublic(BaseModel):
    """The API contract: an allow-list of fields."""

    id: int
    email: str
    first_name: str
    last_name: str

    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


def fake_hash(password: str) -> str:
    return "hashed$" + password[::-1]


USERS: dict[int, UserInDB] = {}


def to_public(user: UserInDB) -> UserPublic:
    # Validating from the internal model's attributes: extra fields are ignored.
    return UserPublic.model_validate(user.model_dump())


@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
def create_user(user: UserCreate, response: Response):
    new_id = max(USERS, default=0) + 1
    data = user.model_dump(exclude={"password"})
    USERS[new_id] = UserInDB(id=new_id, password_hash=fake_hash(user.password), **data)
    response.headers["Location"] = f"/users/{new_id}"
    return to_public(USERS[new_id])


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(404, "User not found")
    return to_public(USERS[user_id])


@app.get("/users", response_model=Page[UserPublic])
def list_users(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    users = list(USERS.values())
    return Page[UserPublic](
        items=[to_public(u) for u in users[offset : offset + limit]],
        total=len(users),
        limit=limit,
        offset=offset,
    )


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int) -> None:
    if USERS.pop(user_id, None) is None:
        raise HTTPException(404, "User not found")
