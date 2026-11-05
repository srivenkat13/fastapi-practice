from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)


def test_app_metadata():
    info = client.get("/openapi.json").json()["info"]
    assert info == {"title": "Bookshelf API", "version": "0.1.0"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_books():
    r = client.get("/books")
    assert r.status_code == 200
    assert len(r.json()) == 3 and r.json()[0]["title"] == "Fluent Python"


def test_docs_metadata():
    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/health"]["get"]["tags"] == ["meta"]
    assert paths["/books"]["get"]["tags"] == ["books"]
    assert paths["/books"]["get"]["summary"] == "List all books"


def test_swagger_ui_is_served():
    assert client.get("/docs").status_code == 200
