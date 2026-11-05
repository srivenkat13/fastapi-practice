import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset():
    main.OPENED.clear()
    main.CALLS["get_current_user"] = 0
    main.app.dependency_overrides.clear()


def test_pagination_dependency_shared_and_validated():
    assert client.get("/books", params={"limit": 2, "offset": 1}).json() == ["Dune", "SPQR"]
    assert client.get("/authors", params={"limit": 1}).json() == ["Ramalho"]
    for path in ("/books", "/authors"):
        assert client.get(path, params={"limit": 0}).status_code == 422
        assert client.get(path, params={"offset": -1}).status_code == 422
    assert hasattr(main, "pagination") and hasattr(main, "PageDep")


def test_db_is_closed_after_success_and_error():
    assert client.get("/books/1").status_code == 200
    assert client.get("/books/99").status_code == 404
    client.get("/books")
    assert len(main.OPENED) == 3
    assert all(db.closed for db in main.OPENED), "get_db must close the DB after every request (use try/finally)"


def test_db_can_be_overridden():
    fake = main.FakeDB(books={7: "Override"})
    main.app.dependency_overrides[main.get_db] = lambda: fake
    assert client.get("/books").json() == ["Override"]


def test_admin_router_guarded():
    for method, path in (("get", "/admin/stats"), ("post", "/admin/reindex")):
        assert client.request(method, path).status_code == 401
        assert client.request(method, path, headers={"X-API-Key": "nope"}).status_code == 401
        assert client.request(method, path, headers={"X-API-Key": "letmein"}).status_code == 200


def test_roles():
    assert client.delete("/books/1").status_code == 401
    assert client.delete("/books/1", headers={"X-User": "bob"}).status_code == 403
    assert client.delete("/books/1", headers={"X-User": "ada"}).status_code == 204


def test_current_user_runs_once_per_request():
    r = client.get("/whoami", headers={"X-User": "bob"})
    assert r.status_code == 200
    assert r.json() == {"name": "bob", "audit": "audited:bob"}
    assert main.CALLS["get_current_user"] == 1


def test_current_user_override():
    main.app.dependency_overrides[main.get_current_user] = lambda: {"name": "test", "roles": ["admin"]}
    assert client.delete("/books/1").status_code == 204
