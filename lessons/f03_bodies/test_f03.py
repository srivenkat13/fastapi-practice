import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)

VALID = {
    "title": "  Fluent Python  ",
    "isbn": "9781492056355",
    "year": 2022,
    "price": 59.99,
    "tags": ["Python", "python ", "Advanced"],
    "author": {"name": "Luciano Ramalho", "email": "luciano@example.com"},
}


@pytest.fixture(autouse=True)
def clean():
    main.BOOKS.clear()


def error_fields(response):
    assert response.status_code == 422, response.text
    return {tuple(str(p) for p in e["loc"][1:]) for e in response.json()["detail"]}


def test_create_normalises():
    r = client.post("/books", json=VALID)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"] == 1
    assert body["title"] == "Fluent Python"
    assert body["tags"] == ["advanced", "python"]
    assert body["author"]["name"] == "Luciano Ramalho"


@pytest.mark.parametrize(
    "change, field",
    [
        ({"title": ""}, ("title",)),
        ({"isbn": "12345"}, ("isbn",)),
        ({"year": 1200}, ("year",)),
        ({"price": 0}, ("price",)),
        ({"tags": ["a", "b", "c", "d", "e", "f"]}, ("tags",)),
        ({"author": {"name": "X", "email": "not-an-email"}}, ("author", "email")),
        ({"author": {"name": ""}}, ("author", "name")),
    ],
)
def test_field_validation(change, field):
    assert field in error_fields(client.post("/books", json={**VALID, **change}))


def test_rejects_unknown_fields():
    assert ("is_admin",) in error_fields(client.post("/books", json={**VALID, "is_admin": True}))


def test_sale_price_must_be_lower():
    r = client.post("/books", json={**VALID, "sale_price": 60})
    assert r.status_code == 422
    assert "sale_price must be lower than price" in r.text
    assert client.post("/books", json={**VALID, "sale_price": 49.99}).status_code == 201


def test_missing_nested_author():
    payload = {k: v for k, v in VALID.items() if k != "author"}
    assert ("author",) in error_fields(client.post("/books", json=payload))


def test_patch_is_partial():
    client.post("/books", json=VALID)
    r = client.patch("/books/1", json={"price": 45, "tags": ["Sale"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["price"] == 45 and body["tags"] == ["sale"]
    assert body["title"] == "Fluent Python" and body["year"] == 2022


def test_patch_validation_and_404():
    client.post("/books", json=VALID)
    assert client.patch("/books/1", json={"price": -1}).status_code == 422
    assert client.patch("/books/1", json={"sale_price": 100}).status_code == 422
    assert client.patch("/books/99", json={"price": 10}).status_code == 404
