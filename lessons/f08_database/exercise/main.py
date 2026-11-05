from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError  # noqa: F401
from sqlalchemy.orm import Session, selectinload  # noqa: F401

from .database import Base, engine, get_session
from .models import Author, Book
from .schemas import AuthorCreate, AuthorOut, BookCreate, BookOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="F08 · Database", lifespan=lifespan)
DB = Annotated[Session, Depends(get_session)]


# ✅ Worked example: study these two endpoints first.
@app.post("/authors", response_model=AuthorOut, status_code=201)
def create_author(data: AuthorCreate, db: DB):
    author = Author(name=data.name)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


@app.get("/authors/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, db: DB):
    author = db.get(Author, author_id)
    if author is None:
        raise HTTPException(404, "Author not found")
    return author


# TODO: POST /books -> 201 BookOut. 404 if author_id doesn't exist; 409 on duplicate ISBN
#       (catch IntegrityError, db.rollback(), raise HTTPException(409, ...)).


@app.get("/books", response_model=list[BookOut])
def list_books(db: DB):
    # 🐛 N+1: serialising each book's `author` triggers one extra SELECT per book.
    #    Fix with .options(selectinload(Book.author)).
    return db.scalars(select(Book).order_by(Book.id)).all()


# TODO: GET /books/{book_id} -> BookOut or 404

# TODO: GET /authors/{author_id}/books -> that author's books ordered by year; 404 if no such author
