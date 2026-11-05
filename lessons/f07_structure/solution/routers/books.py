from fastapi import APIRouter, HTTPException

from ..data import BOOKS

router = APIRouter(prefix="/books", tags=["books"])


@router.get("")
def list_books():
    return list(BOOKS.values())


@router.get("/{book_id}")
def get_book(book_id: int):
    if book_id not in BOOKS:
        raise HTTPException(404, "Book not found")
    return BOOKS[book_id]
