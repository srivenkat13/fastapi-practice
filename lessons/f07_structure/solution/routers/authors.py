from fastapi import APIRouter, HTTPException

from ..data import AUTHORS, BOOKS

router = APIRouter(prefix="/authors", tags=["authors"])


@router.get("")
def list_authors():
    return list(AUTHORS.values())


@router.get("/{author_id}/books")
def author_books(author_id: int):
    if author_id not in AUTHORS:
        raise HTTPException(404, "Author not found")
    return [b for b in BOOKS.values() if b["author_id"] == author_id]
