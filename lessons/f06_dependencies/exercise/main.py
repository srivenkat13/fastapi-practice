from dataclasses import dataclass, field
from typing import Annotated  # noqa: F401

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query  # noqa: F401

app = FastAPI(title="F06 · Dependencies")


# ---- a pretend database -------------------------------------------------------
@dataclass
class FakeDB:
    books: dict = field(default_factory=lambda: {1: "Fluent Python", 2: "Dune", 3: "SPQR", 4: "Foundation"})
    authors: list = field(default_factory=lambda: ["Ramalho", "Herbert", "Beard", "Asimov"])
    closed: bool = False

    def close(self):
        self.closed = True


OPENED: list[FakeDB] = []  # tests inspect this to check every DB got closed


def open_db() -> FakeDB:
    db = FakeDB()
    OPENED.append(db)
    return db


# TODO 2: get_db() yield dependency: db = open_db(); yield it; ALWAYS db.close()


# TODO 1: Pagination dataclass + pagination(limit 1..100 default 20, offset >= 0 default 0) + PageDep alias


@app.get("/books")
def list_books(limit: int = 20, offset: int = 0):  # 🐛 duplicated, unvalidated, never closes the db
    db = open_db()
    items = list(db.books.values())
    return items[offset : offset + limit]


@app.get("/authors")
def list_authors(limit: int = 20, offset: int = 0):  # 🐛 duplicated, unvalidated, never closes the db
    db = open_db()
    return db.authors[offset : offset + limit]


@app.get("/books/{book_id}")
def get_book(book_id: int):
    db = open_db()
    if book_id not in db.books:
        raise HTTPException(404, "Book not found")  # with get_db, the DB must still be closed on errors
    return {"id": book_id, "title": db.books[book_id]}


# TODO 4: get_current_user(x_user header) -> {"name": ..., "roles": [...]} using USERS; 401 if header missing/unknown
#         require_role(role) factory -> dependency raising 403 if the user lacks the role
USERS = {"ada": ["admin", "reader"], "bob": ["reader"]}
CALLS = {"get_current_user": 0}  # increment inside get_current_user; tests check caching


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):  # TODO: require role "admin"
    return None


# TODO 5: /whoami: depends on get_current_user AND audit_user (which itself depends on get_current_user)
def audit_user():
    return "audited"


@app.get("/whoami")
def whoami():
    return {"name": None, "audit": audit_user()}


# TODO 3: guard the whole router with require_api_key (X-API-Key must be "letmein", else 401)
admin = APIRouter(prefix="/admin")


@admin.get("/stats")
def stats(x_api_key: str | None = Header(default=None)):  # 🐛 manual check in every route
    if x_api_key != "letmein":
        raise HTTPException(401, "Invalid API key")
    return {"books": 4}


@admin.post("/reindex")
def reindex():  # 🐛 forgot the check entirely
    return {"status": "reindexing"}


app.include_router(admin)
