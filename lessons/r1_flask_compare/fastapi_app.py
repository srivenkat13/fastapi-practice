"""The reference: a small books API in FastAPI. Your job is to rebuild it in Flask (exercise/flask_app.py)."""
import uuid
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

BOOKS = [
    {"id": 1, "title": "Fluent Python", "genre": "tech", "year": 2022},
    {"id": 2, "title": "Dune", "genre": "fiction", "year": 1965},
]


class BookIn(BaseModel):
    title: str = Field(min_length=1)
    genre: str = "tech"
    year: int = Field(ge=1450, le=2100)


app = FastAPI(title="R1 · FastAPI reference")


@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.get("/books")
def list_books(genre: str | None = None):
    return [b for b in BOOKS if genre is None or b["genre"] == genre]


@app.get("/books/{book_id}")
def get_book(book_id: int):
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    raise HTTPException(404, "Book not found")


@app.post("/books", status_code=201)
def create_book(data: BookIn, x_api_key: Annotated[str | None, Header()] = None):
    if x_api_key != "letmein":
        raise HTTPException(401, "Invalid API key")
    book = {"id": len(BOOKS) + 1, **data.model_dump()}
    BOOKS.append(book)
    return book
