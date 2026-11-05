from datetime import date, datetime  # noqa: F401
from enum import Enum
from typing import Generic, TypeVar  # noqa: F401

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# TODO: ProjectCreate, ProjectUpdate, ProjectOut (id, name, description, owner_id, members: list[UserOut]), AddMember
# TODO: TaskCreate, TaskUpdate, TaskOut, Page[T]  (see the README for fields and rules; forbid extra fields!)
