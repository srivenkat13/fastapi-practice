from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .database import Base, engine, get_session
from .models import Author, Book
from .schemas import AuthorCreate, AuthorOut, BookCreate, BookOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # dev convenience; real projects use Alembic migrations
    yield


app = FastAPI(title="F08 · Database", lifespan=lifespan)
DB = Annotated[Session, Depends(get_session)]


@app.post("/authors", response_model=AuthorOut, status_code=201)
def create_author(data: AuthorCreate, db: DB):
    author = Author(name=data.name)
    db.add(author)
    db.commit()
    db.refresh(author)  # load DB-generated values (the id)
    return author


@app.get("/authors/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, db: DB):
    author = db.get(Author, author_id)  # primary-key lookup (uses the identity map)
    if author is None:
        raise HTTPException(404, "Author not found")
    return author


@app.post("/books", response_model=BookOut, status_code=201)
def create_book(data: BookCreate, db: DB):
    if db.get(Author, data.author_id) is None:
        raise HTTPException(404, "Author not found")
    book = Book(**data.model_dump())
    db.add(book)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A book with this ISBN already exists")
    db.refresh(book)
    return book


@app.get("/books", response_model=list[BookOut])
def list_books(db: DB):
    # selectinload: 1 query for books + 1 query for ALL their authors (instead of 1 per book = N+1)
    stmt = select(Book).options(selectinload(Book.author)).order_by(Book.id)
    return db.scalars(stmt).all()


@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: DB):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    return book


@app.get("/authors/{author_id}/books", response_model=list[BookOut])
def author_books(author_id: int, db: DB):
    if db.get(Author, author_id) is None:
        raise HTTPException(404, "Author not found")
    stmt = select(Book).where(Book.author_id == author_id).options(selectinload(Book.author)).order_by(Book.year)
    return db.scalars(stmt).all()
