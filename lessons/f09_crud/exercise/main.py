"""HTTP layer: thin. Parses input, calls crud.py, shapes output. (Already complete; your work is in crud.py.)"""
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from sqlalchemy.orm import Session

from . import crud
from .database import Base, engine, get_session
from .schemas import BookCreate, BookOut, BookPatch, Genre, Page


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="F09 · CRUD", lifespan=lifespan)
DB = Annotated[Session, Depends(get_session)]


def book_or_404(book_id: int, db: DB):
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    return book


@app.post("/books", response_model=BookOut, status_code=201)
def create_book(data: BookCreate, db: DB, response: Response):
    try:
        book = crud.create_book(db, data)
    except crud.DuplicateISBN:
        raise HTTPException(409, "A book with this ISBN already exists")
    response.headers["Location"] = f"/books/{book.id}"
    return book


@app.get("/books", response_model=Page[BookOut])
def list_books(
    db: DB,
    q: Annotated[str | None, Query(description="Search title or author")] = None,
    genre: Genre | None = None,
    min_year: int | None = None,
    max_year: int | None = None,
    sort: Annotated[str, Query(description="Comma-separated fields; prefix '-' for descending, e.g. -year,title")] = "id",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        order_by = crud.parse_sort(sort)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    filters = crud.BookFilters(q=q, genre=genre, min_year=min_year, max_year=max_year)
    items, total = crud.list_books(db, filters, order_by, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book=Depends(book_or_404)):
    return book


@app.put("/books/{book_id}", response_model=BookOut)
def replace_book(data: BookCreate, db: DB, book=Depends(book_or_404)):
    try:
        return crud.update_book(db, book, data.model_dump())
    except crud.DuplicateISBN:
        raise HTTPException(409, "A book with this ISBN already exists")


@app.patch("/books/{book_id}", response_model=BookOut)
def patch_book(data: BookPatch, db: DB, book=Depends(book_or_404)):
    return crud.update_book(db, book, data.model_dump(exclude_unset=True))


@app.delete("/books/{book_id}", status_code=204)
def delete_book(db: DB, book=Depends(book_or_404)) -> None:
    crud.delete_book(db, book)
