from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query

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

PageLimit = Annotated[int, Query(ge=1, le=50, description="Page size")]


# Fixed paths first: they must be declared before /books/{book_id}.
@app.get("/books/featured")
def featured_books():
    return [b for b in BOOKS if b["featured"]]


@app.get("/books/{book_id}")
def get_book(book_id: Annotated[int, Path(gt=0, description="The book's ID")]):
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")


@app.get("/books")
def list_books(
    q: Annotated[str | None, Query(min_length=1, description="Title contains (case-insensitive)")] = None,
    genre: Genre | None = None,
    min_year: Annotated[int | None, Query(ge=1450)] = None,
    tags: Annotated[list[str], Query(alias="tag")] = [],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: PageLimit = 10,
):
    results = BOOKS
    if q:
        results = [b for b in results if q.lower() in b["title"].lower()]
    if genre:
        results = [b for b in results if b["genre"] == genre.value]
    if min_year is not None:
        results = [b for b in results if b["year"] >= min_year]
    if tags:
        results = [b for b in results if set(tags) <= set(b["tags"])]
    return results[offset : offset + limit]


@app.get("/genres/{genre}/count")
def count_genre(genre: Genre):
    return {"genre": genre, "count": sum(b["genre"] == genre.value for b in BOOKS)}
