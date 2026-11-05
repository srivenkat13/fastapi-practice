from fastapi import FastAPI, HTTPException  # noqa: F401
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator  # noqa: F401

app = FastAPI(title="F03 · Bodies")


class AuthorIn(BaseModel):
    # TODO: name (1-100 chars), email (optional, must be a valid email)
    name: str
    email: str | None = None


class BookCreate(BaseModel):
    """TODO:
    - reject unknown fields (extra="forbid") and strip whitespace from strings
    - title: 1..200 chars
    - isbn: exactly 13 digits
    - year: 1450..2100
    - price: > 0
    - sale_price: optional, must be lower than price (model_validator)
    - tags: default [], at most 5; normalise to sorted, unique, lower-case, stripped (field_validator)
    - author: AuthorIn (nested)
    """

    title: str
    isbn: str
    year: int
    price: float
    sale_price: float | None = None
    tags: list[str] = []
    author: AuthorIn


class BookUpdate(BaseModel):
    """TODO: every field optional (title, price, sale_price, tags), with the same constraints as BookCreate."""


BOOKS: dict[int, dict] = {}


# TODO: POST /books -> 201, store book.model_dump() plus an "id" (len(BOOKS) + 1), return it


# TODO: PATCH /books/{book_id} -> apply only the fields the client sent; 404 if the book is missing.
#       Re-check the sale_price < price rule after merging (return 422 with HTTPException if violated).
