from datetime import date, datetime
from enum import Enum
from typing import Generic, TypeVar

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


# ---- users ---------------------------------------------------------------------------------
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


# ---- projects ------------------------------------------------------------------------------
class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    owner_id: int
    members: list[UserOut]


class AddMember(BaseModel):
    email: EmailStr


# ---- tasks ---------------------------------------------------------------------------------
class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)  # store "todo", not Status.todo
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    status: Status = Status.todo
    priority: Priority = Priority.medium
    due_date: date | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: Status | None = None
    priority: Priority | None = None
    due_date: date | None = None
    assignee_id: int | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    title: str
    description: str
    status: Status
    priority: Priority
    due_date: date | None
    assignee_id: int | None
    created_by_id: int
    created_at: datetime
    completed_at: datetime | None


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
