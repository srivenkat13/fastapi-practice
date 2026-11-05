import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from support import target

database = target(__file__, "database")
crud = target(__file__, "crud")
main = target(__file__, "main")

BOOKS = [
    ("Fluent Python", "Luciano Ramalho", "tech", 2022, 5999, "9781492056355"),
    ("Dune", "Frank Herbert", "fiction", 1965, 1099, "9780441013593"),
    ("Python Crash Course", "Eric Matthes", "tech", 2019, 3999, "9781593279288"),
    ("SPQR", "Mary Beard", "history", 2015, 1899, "9781631492228"),
    ("Foundation", "Isaac Asimov", "fiction", 1951, 899, "9780553293357"),
    ("A Brief History of Time", "Stephen Hawking", "science", 1988, 1599, "9780553380163"),
]


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with TestSession() as s:
            yield s

    main.app.dependency_overrides[database.get_session] = override
    c = TestClient(main.app)
    for title, author, genre, year, price, isbn in BOOKS:
        r = c.post("/books", json={"title": title, "author": author, "genre": genre, "year": year, "price_cents": price, "isbn": isbn})
        assert r.status_code == 201, r.text
    yield c
    main.app.dependency_overrides.clear()


def titles(r):
    assert r.status_code == 200, r.text
    return [b["title"] for b in r.json()["items"]]


def test_parse_sort_whitelist():
    assert len(crud.parse_sort("-year,title")) == 2
    assert crud.parse_sort("") == []
    with pytest.raises(ValueError, match="password"):
        crud.parse_sort("password")


def test_create_location_and_duplicate(client):
    r = client.post("/books", json={"title": "X", "author": "Y", "genre": "tech", "year": 2000, "price_cents": 1, "isbn": "1111111111111"})
    assert r.status_code == 201 and r.headers["location"] == "/books/7"
    dup = {"title": "X", "author": "Y", "genre": "tech", "year": 2000, "price_cents": 1, "isbn": "9780441013593"}
    assert client.post("/books", json=dup).status_code == 409


def test_list_envelope_and_pagination(client):
    page = client.get("/books", params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 6 and page["limit"] == 2 and page["offset"] == 2
    assert [b["title"] for b in page["items"]] == ["Python Crash Course", "SPQR"]


def test_filters_and_total(client):
    r = client.get("/books", params={"q": "python"})
    assert titles(r) == ["Fluent Python", "Python Crash Course"] and r.json()["total"] == 2
    assert titles(client.get("/books", params={"q": "HERBERT"})) == ["Dune"]
    assert titles(client.get("/books", params={"genre": "fiction"})) == ["Dune", "Foundation"]
    r = client.get("/books", params={"min_year": 1960, "max_year": 2016, "limit": 1})
    assert titles(r) == ["Dune"] and r.json()["total"] == 3, "total ignores limit/offset"


def test_sorting(client):
    assert titles(client.get("/books", params={"sort": "-year", "limit": 3})) == ["Fluent Python", "Python Crash Course", "SPQR"]
    assert client.get("/books", params={"sort": "genre"}).status_code == 422, "genre is not in SORTABLE"
    by_price = titles(client.get("/books", params={"sort": "price_cents", "limit": 2}))
    assert by_price == ["Foundation", "Dune"]


def test_get_put_patch_delete(client):
    assert client.get("/books/2").json()["title"] == "Dune"
    assert client.get("/books/99").status_code == 404

    full = {"title": "Dune (Deluxe)", "author": "Frank Herbert", "genre": "fiction", "year": 1965, "price_cents": 2599, "isbn": "9780441013593"}
    assert client.put("/books/2", json=full).json()["price_cents"] == 2599
    assert client.put("/books/2", json={"title": "only title"}).status_code == 422, "PUT requires every field"
    assert client.put("/books/2", json={**full, "isbn": "9781492056355"}).status_code == 409

    r = client.patch("/books/2", json={"price_cents": 999})
    assert r.json()["price_cents"] == 999 and r.json()["title"] == "Dune (Deluxe)"

    assert client.delete("/books/2").status_code == 204
    assert client.get("/books/2").status_code == 404
    assert client.get("/books").json()["total"] == 5
