"""Data access for books."""
from dataclasses import dataclass

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Book
from .schemas import BookCreate

SORTABLE = {"id", "title", "year", "price_cents"}


class DuplicateISBN(Exception):
    pass


@dataclass
class BookFilters:
    q: str | None = None
    genre: str | None = None
    min_year: int | None = None
    max_year: int | None = None

    def apply(self, stmt):
        if self.q:
            pattern = f"%{self.q}%"  # bound parameter → no SQL injection
            stmt = stmt.where(or_(Book.title.ilike(pattern), Book.author.ilike(pattern)))
        if self.genre:
            stmt = stmt.where(Book.genre == self.genre)
        if self.min_year is not None:
            stmt = stmt.where(Book.year >= self.min_year)
        if self.max_year is not None:
            stmt = stmt.where(Book.year <= self.max_year)
        return stmt


def parse_sort(sort: str) -> list:
    clauses = []
    for part in (p.strip() for p in sort.split(",")):
        if not part:
            continue
        direction, field = (desc, part[1:]) if part.startswith("-") else (asc, part)
        if field not in SORTABLE:
            raise ValueError(f"Cannot sort by '{field}'")
        clauses.append(direction(getattr(Book, field)))
    return clauses


def _commit(db: Session, book: Book) -> Book:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateISBN()
    db.refresh(book)
    return book


def create_book(db: Session, data: BookCreate) -> Book:
    book = Book(**data.model_dump())
    db.add(book)
    return _commit(db, book)


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def list_books(db: Session, filters: BookFilters, order_by: list, limit: int, offset: int) -> tuple[list[Book], int]:
    base = filters.apply(select(Book))
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    page = base.order_by(*order_by, Book.id).limit(limit).offset(offset)
    return list(db.scalars(page)), total


def update_book(db: Session, book: Book, changes: dict) -> Book:
    for field, value in changes.items():
        setattr(book, field, value)
    return _commit(db, book)


def delete_book(db: Session, book: Book) -> None:
    db.delete(book)
    db.commit()
