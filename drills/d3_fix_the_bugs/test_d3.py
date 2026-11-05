import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)
TOKEN = {"X-Token": "secret-owner-token"}


@pytest.fixture(autouse=True)
def reset():
    main.NOTES.clear()


def create(title="Note", tags=()):
    return client.post("/notes", json={"title": title, "tags": list(tags)}, headers=TOKEN)


def test_create_status_and_no_leak():
    r = create("Groceries", ["Food"])
    assert r.status_code == 201
    assert r.json() == {"id": 1, "title": "Groceries", "body": "", "tags": ["food"]}
    assert "secret-owner-token" not in r.text
    assert client.post("/notes", json={"title": "x"}).status_code == 401


def test_tags_do_not_leak_between_notes():
    create("A", ["Work", "work "])
    r = create("B", ["Home"])
    assert r.json()["tags"] == ["home"]
    assert client.get("/notes/1").json()["tags"] == ["work"]


def test_stats_route():
    create("A", ["x"])
    r = client.get("/notes/stats")
    assert r.status_code == 200 and r.json() == {"count": 1, "tags": ["x"]}


def test_pagination_and_search():
    for i in range(5):
        create(f"Python note {i}")
    create("Shopping list")
    assert len(client.get("/notes", params={"limit": 3}).json()) == 3
    assert [n["id"] for n in client.get("/notes", params={"limit": 2, "offset": 4}).json()] == [5, 6]
    assert len(client.get("/notes", params={"q": "python"}).json()) == 5


def test_patch_is_partial():
    client.post("/notes", json={"title": "T", "body": "keep me", "tags": ["a"]}, headers=TOKEN)
    r = client.patch("/notes/1", json={"title": "New title"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "title": "New title", "body": "keep me", "tags": ["a"]}
    assert client.patch("/notes/1", json={"tags": ["B"]}).json()["tags"] == ["b"]


def test_delete():
    create()
    r = client.delete("/notes/1")
    assert r.status_code == 204 and r.content == b""
    assert client.delete("/notes/1").status_code == 404
