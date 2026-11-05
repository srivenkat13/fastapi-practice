from dataclasses import dataclass, field
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query

app = FastAPI(title="F06 · Dependencies")


@dataclass
class FakeDB:
    books: dict = field(default_factory=lambda: {1: "Fluent Python", 2: "Dune", 3: "SPQR", 4: "Foundation"})
    authors: list = field(default_factory=lambda: ["Ramalho", "Herbert", "Beard", "Asimov"])
    closed: bool = False

    def close(self):
        self.closed = True


OPENED: list[FakeDB] = []


def open_db() -> FakeDB:
    db = FakeDB()
    OPENED.append(db)
    return db


# ---- dependencies --------------------------------------------------------------
def get_db():
    db = open_db()
    try:
        yield db
    finally:
        db.close()


DB = Annotated[FakeDB, Depends(get_db)]


@dataclass
class Pagination:
    limit: int
    offset: int

    def apply(self, items: list) -> list:
        return items[self.offset : self.offset + self.limit]


def pagination(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Pagination:
    return Pagination(limit, offset)


PageDep = Annotated[Pagination, Depends(pagination)]

USERS = {"ada": ["admin", "reader"], "bob": ["reader"]}
CALLS = {"get_current_user": 0}


def get_current_user(x_user: Annotated[str | None, Header()] = None) -> dict:
    CALLS["get_current_user"] += 1
    if x_user not in USERS:
        raise HTTPException(401, "Not authenticated")
    return {"name": x_user, "roles": USERS[x_user]}


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_role(role: str):
    def checker(user: CurrentUser) -> dict:
        if role not in user["roles"]:
            raise HTTPException(403, f"Requires role '{role}'")
        return user

    return checker


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if x_api_key != "letmein":
        raise HTTPException(401, "Invalid API key")


def audit_user(user: CurrentUser) -> str:
    return f"audited:{user['name']}"


# ---- routes ----------------------------------------------------------------------
@app.get("/books")
def list_books(db: DB, page: PageDep):
    return page.apply(list(db.books.values()))


@app.get("/authors")
def list_authors(db: DB, page: PageDep):
    return page.apply(db.authors)


@app.get("/books/{book_id}")
def get_book(book_id: int, db: DB):
    if book_id not in db.books:
        raise HTTPException(404, "Book not found")
    return {"id": book_id, "title": db.books[book_id]}


@app.delete("/books/{book_id}", status_code=204, dependencies=[Depends(require_role("admin"))])
def delete_book(book_id: int) -> None:
    return None


@app.get("/whoami")
def whoami(user: CurrentUser, audit: Annotated[str, Depends(audit_user)]):
    return {"name": user["name"], "audit": audit}


admin = APIRouter(prefix="/admin", dependencies=[Depends(require_api_key)])


@admin.get("/stats")
def stats():
    return {"books": 4}


@admin.post("/reindex")
def reindex():
    return {"status": "reindexing"}


app.include_router(admin)
