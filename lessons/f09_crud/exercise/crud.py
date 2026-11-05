"""Data access for books. Implement every function; main.py already calls them."""
from dataclasses import dataclass

from sqlalchemy import asc, desc, func, or_, select  # noqa: F401
from sqlalchemy.exc import IntegrityError  # noqa: F401
from sqlalchemy.orm import Session

from .models import Book
from .schemas import BookCreate

SORTABLE = {"id", "title", "year", "price_cents"}  # whitelist: never sort by arbitrary user input


class DuplicateISBN(Exception):
    pass


@dataclass
class BookFilters:
    q: str | None = None
    genre: str | None = None
    min_year: int | None = None
    max_year: int | None = None


def parse_sort(sort: str) -> list:
    """"-year,title" -> [desc(Book.year), asc(Book.title)].
    Raise ValueError(f"Cannot sort by '{field}'") for fields not in SORTABLE. Ignore empty parts."""
    raise NotImplementedError


def create_book(db: Session, data: BookCreate) -> Book:
    """Insert and return the book. On IntegrityError: rollback and raise DuplicateISBN."""
    raise NotImplementedError


def get_book(db: Session, book_id: int) -> Book | None:
    raise NotImplementedError


def list_books(db: Session, filters: BookFilters, order_by: list, limit: int, offset: int) -> tuple[list[Book], int]:
    """Return (page_of_books, total_matching_count).
    - q: case-insensitive match in title OR author (Book.title.ilike(f"%{q}%"))
    - genre / min_year / max_year: exact / >= / <=
    - total counts ALL matching rows (ignoring limit/offset)
    - always add Book.id as a final tie-breaker so pagination is stable
    """
    raise NotImplementedError


def update_book(db: Session, book: Book, changes: dict) -> Book:
    """Apply changes (setattr), commit, refresh, return. IntegrityError -> rollback + DuplicateISBN."""
    raise NotImplementedError


def delete_book(db: Session, book: Book) -> None:
    raise NotImplementedError
