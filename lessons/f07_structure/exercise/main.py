"""🐛 Everything in one file, config read straight from os.environ, no versioning.

Refactor into:
  config.py          Settings(BaseSettings) + get_settings()
  routers/books.py   router = APIRouter(prefix="/books", tags=["books"])
  routers/authors.py router = APIRouter(prefix="/authors", tags=["authors"])
  routers/meta.py    router = APIRouter(tags=["meta"]) with GET /info
  main.py            app = FastAPI(...) + include each router under prefix "/api/v1"
See the README for the exact requirements.
"""
import os

from fastapi import FastAPI, HTTPException

from .data import AUTHORS, BOOKS

app = FastAPI(title=os.environ.get("BOOKSHELF_APP_NAME", "Bookshelf"))


@app.get("/books")
def list_books():
    return list(BOOKS.values())


@app.get("/books/{book_id}")
def get_book(book_id: int):
    if book_id not in BOOKS:
        raise HTTPException(404, "Book not found")
    return BOOKS[book_id]


@app.get("/authors")
def list_authors():
    return list(AUTHORS.values())


@app.get("/authors/{author_id}/books")
def author_books(author_id: int):
    if author_id not in AUTHORS:
        raise HTTPException(404, "Author not found")
    return [b for b in BOOKS.values() if b["author_id"] == author_id]


@app.get("/info")
def info():
    return {"app_name": os.environ.get("BOOKSHELF_APP_NAME", "Bookshelf"), "debug": os.environ.get("BOOKSHELF_DEBUG") == "1"}
