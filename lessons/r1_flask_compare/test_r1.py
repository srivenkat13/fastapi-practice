import pytest
from fastapi.testclient import TestClient

from lessons.r1_flask_compare import fastapi_app
from support import target

flask_module = target(__file__, "flask_app")
KEY = {"X-API-Key": "letmein"}


@pytest.fixture
def app():
    return flask_module.create_app()


@pytest.fixture
def client(app):
    return app.test_client()


def test_factory_and_blueprint(app):
    assert "books" in app.blueprints
    assert app.config["API_KEY"] == "letmein"
    assert flask_module.create_app({"API_KEY": "other"}).config["API_KEY"] == "other"


def test_list_and_filter(client):
    assert [b["id"] for b in client.get("/books").get_json()] == [1, 2]
    assert [b["id"] for b in client.get("/books?genre=fiction").get_json()] == [2]


def test_get_and_404s(client):
    assert client.get("/books/1").get_json()["title"] == "Fluent Python"
    r = client.get("/books/99")
    assert r.status_code == 404 and r.get_json() == {"detail": "Book not found"}
    r = client.get("/nope")
    assert r.status_code == 404 and r.is_json and r.get_json() == {"detail": "Not Found"}


def test_create_auth_and_validation(client):
    good = {"title": "SPQR", "genre": "history", "year": 2015}
    assert client.post("/books", json=good).status_code == 401
    r = client.post("/books", json=good, headers=KEY)
    assert r.status_code == 201 and r.get_json() == {"id": 3, **good}
    bad = client.post("/books", json={"title": "", "year": 3000}, headers=KEY)
    assert bad.status_code == 422 and set(bad.get_json()["detail"]) == {"title", "year"}
    assert client.post("/books", data="not json", headers=KEY).status_code == 422
    assert client.post("/books", json={"title": "X", "year": "2000"}, headers=KEY).status_code == 422
    defaulted = client.post("/books", json={"title": "X", "year": 2000}, headers=KEY)
    assert defaulted.get_json()["genre"] == "tech"


def test_apps_are_isolated():
    a, b = flask_module.create_app().test_client(), flask_module.create_app().test_client()
    a.post("/books", json={"title": "Only in A", "year": 2000}, headers=KEY)
    assert len(a.get("/books").get_json()) == 3 and len(b.get("/books").get_json()) == 2


def test_request_id(client):
    assert len(client.get("/books").headers["X-Request-ID"]) == 32
    assert client.get("/books/1", headers={"X-Request-ID": "abc"}).headers["X-Request-ID"] == "abc"


def test_parity_with_fastapi(client):
    fast = TestClient(fastapi_app.app)
    for path in ("/books", "/books?genre=tech", "/books/2", "/books/99"):
        f, k = fast.get(path), client.get(path)
        assert (f.status_code, f.json()) == (k.status_code, k.get_json()), path
