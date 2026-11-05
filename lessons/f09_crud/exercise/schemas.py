from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")
Genre = Literal["tech", "fiction", "history", "science"]


class BookCreate(BaseModel):
    """Also used for PUT (full replacement: every field required)."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    genre: Genre
    year: int = Field(ge=1450, le=2100)
    price_cents: int = Field(ge=0)
    isbn: str = Field(pattern=r"^\d{13}$")


class BookPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    genre: Genre | None = None
    year: int | None = Field(default=None, ge=1450, le=2100)
    price_cents: int | None = Field(default=None, ge=0)


class BookOut(BookCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
