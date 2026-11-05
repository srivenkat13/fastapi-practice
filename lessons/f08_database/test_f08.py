import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from support import target

database = target(__file__, "database")
models = target(__file__, "models")
main = target(__file__, "main")

SESSIONS = []


class TrackingSession(Session):
    """Records every session opened and whether it was closed."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed_by_app = False
        SESSIONS.append(self)

    def close(self):
        self.closed_by_app = True
        super().close()


@pytest.fixture
def ctx():
    # A fresh in-memory DB per test. StaticPool keeps one connection, so every session sees the same DB.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, class_=TrackingSession)
    selects = []
    event.listen(engine, "before_cursor_execute", lambda *a: a[2].lstrip().upper().startswith("SELECT") and selects.append(a[2]))

    real_sessionmaker = database.SessionLocal
    database.SessionLocal = TestSession  # so the learner's own get_session uses the test DB
    SESSIONS.clear()
    try:
        yield TestClient(main.app), selects
    finally:
        database.SessionLocal = real_sessionmaker


def seed(client):
    a1 = client.post("/authors", json={"name": "Frank Herbert"}).json()["id"]
    a2 = client.post("/authors", json={"name": "Isaac Asimov"}).json()["id"]
    books = [("Dune", "9780441013593", 1965, a1), ("Dune Messiah", "9780593098233", 1969, a1),
             ("Foundation", "9780553293357", 1951, a2), ("I, Robot", "9780553382563", 1950, a2)]
    for title, isbn, year, author in books:
        r = client.post("/books", json={"title": title, "isbn": isbn, "year": year, "author_id": author})
        assert r.status_code == 201, r.text
    return a1, a2


def test_models_have_relationships():
    assert "author_id" in models.Book.__table__.c
    fks = {fk.target_fullname for fk in models.Book.__table__.c.author_id.foreign_keys}
    assert fks == {"authors.id"}
    assert models.Book.__table__.c.isbn.unique
    assert hasattr(models.Author, "books") and hasattr(models.Book, "author")


def test_create_and_get_book(ctx):
    client, _ = ctx
    seed(client)
    r = client.get("/books/1")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "title": "Dune", "isbn": "9780441013593", "year": 1965, "author": {"id": 1, "name": "Frank Herbert"}}
    assert client.get("/books/99").status_code == 404


def test_create_book_errors(ctx):
    client, _ = ctx
    seed(client)
    payload = {"title": "X", "isbn": "9780441013593", "year": 2000, "author_id": 1}
    assert client.post("/books", json=payload).status_code == 409
    assert client.post("/books", json={**payload, "isbn": "1111111111111", "author_id": 99}).status_code == 404
    assert client.post("/books", json={**payload, "isbn": "1111111111111"}).status_code == 201, "session must be usable after a rollback"


def test_author_books(ctx):
    client, _ = ctx
    _, asimov = seed(client)
    assert [b["title"] for b in client.get(f"/authors/{asimov}/books").json()] == ["I, Robot", "Foundation"]
    assert client.get("/authors/99/books").status_code == 404


def test_list_books_has_no_n_plus_1(ctx):
    client, selects = ctx
    seed(client)
    selects.clear()
    r = client.get("/books")
    assert [b["author"]["name"] for b in r.json()] == ["Frank Herbert", "Frank Herbert", "Isaac Asimov", "Isaac Asimov"]
    assert len(selects) <= 2, f"expected ≤ 2 SELECTs (books + authors), got {len(selects)}: N+1 problem"


def test_sessions_are_closed(ctx):
    client, _ = ctx
    client.post("/authors", json={"name": "A"})
    client.get("/authors/1")
    client.get("/authors/42")
    assert SESSIONS, "requests should open sessions via database.SessionLocal"
    assert all(s.closed_by_app for s in SESSIONS), "get_session must close every session"
