from enum import Enum
from typing import Annotated  # noqa: F401

from fastapi import FastAPI, HTTPException, Path, Query  # noqa: F401

app = FastAPI(title="F02 · Params")


class Genre(str, Enum):
    tech = "tech"
    fiction = "fiction"
    history = "history"


BOOKS = [
    {"id": 1, "title": "Fluent Python", "genre": "tech", "year": 2022, "tags": ["python", "advanced"], "featured": True},
    {"id": 2, "title": "Dune", "genre": "fiction", "year": 1965, "tags": ["classic", "scifi"], "featured": False},
    {"id": 3, "title": "Python Crash Course", "genre": "tech", "year": 2019, "tags": ["python", "beginner"], "featured": False},
    {"id": 4, "title": "SPQR", "genre": "history", "year": 2015, "tags": ["rome"], "featured": True},
    {"id": 5, "title": "Foundation", "genre": "fiction", "year": 1951, "tags": ["classic", "scifi"], "featured": False},
]


@app.get("/books/{book_id}")
def get_book(book_id: int):
    # TODO: book_id must be > 0 (Path(gt=0)); return 404 {"detail": "Book not found"} if missing
    return next(b for b in BOOKS if b["id"] == book_id)


@app.get("/books/featured")  # 🐛 GET /books/featured returns 422. Why?
def featured_books():
    return [b for b in BOOKS if b["featured"]]


@app.get("/books")
def list_books():
    # TODO: q, genre, min_year, tag (repeatable, alias "tag"), offset, limit
    return BOOKS


# TODO: GET /genres/{genre}/count -> {"genre": "tech", "count": 2}
