import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)
SECRET_KEYS = {"password", "password_hash", "internal_notes"}


@pytest.fixture(autouse=True)
def clean():
    main.USERS.clear()


def create(first="Ada", last="Lovelace", email="ada@example.com"):
    return client.post("/users", json={"email": email, "first_name": first, "last_name": last, "password": "s3cret!"})


def test_create_returns_201_with_location():
    r = create()
    assert r.status_code == 201, r.text
    assert r.headers["location"] == "/users/1"
    body = r.json()
    assert body == {
        "id": 1,
        "email": "ada@example.com",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "display_name": "Ada Lovelace",
    }


def test_get_does_not_leak():
    create()
    main.USERS[1].internal_notes = "VIP, gave us a bad review"
    body = client.get("/users/1").json()
    assert not SECRET_KEYS & body.keys()
    assert body["display_name"] == "Ada Lovelace"


def test_list_is_paginated_envelope():
    for i in range(5):
        create(first=f"U{i}", email=f"u{i}@example.com")
    page = client.get("/users", params={"limit": 2, "offset": 1}).json()
    assert page["total"] == 5 and page["limit"] == 2 and page["offset"] == 1
    assert [u["first_name"] for u in page["items"]] == ["U1", "U2"]
    assert not SECRET_KEYS & page["items"][0].keys()
    assert client.get("/users", params={"limit": 0}).status_code == 422


def test_delete_returns_204_empty():
    create()
    r = client.delete("/users/1")
    assert r.status_code == 204 and r.content == b""
    assert client.delete("/users/1").status_code == 404
    assert client.get("/users/1").status_code == 404


def test_openapi_response_schema_hides_secrets():
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    public = next(v for k, v in schemas.items() if k.startswith("UserPublic"))
    assert "password_hash" not in public["properties"]
    assert "display_name" in public["properties"]
