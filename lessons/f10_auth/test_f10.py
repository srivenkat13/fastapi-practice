import base64
import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from support import target

security = target(__file__, "security")
store = target(__file__, "store")
main = target(__file__, "main")
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset():
    store.reset(security.hash_password("adminpass123"))


def login(email, password):
    return client.post("/auth/token", data={"username": email, "password": password})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def register_and_login(email="ada@example.com", password="correct-horse"):
    assert client.post("/auth/register", json={"email": email, "password": password}).status_code == 201
    r = login(email, password)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_password_hashing():
    h1, h2 = security.hash_password("s3cret-pass"), security.hash_password("s3cret-pass")
    assert h1 != "s3cret-pass" and h1 != h2, "hashes must be salted"
    assert h1.startswith("$argon2")
    assert security.verify_password("s3cret-pass", h1)
    assert not security.verify_password("wrong", h1)


def test_tokens_roundtrip_and_expire():
    claims = security.decode_access_token(security.create_access_token("42", "user"))
    assert claims["sub"] == "42" and claims["role"] == "user" and "exp" in claims
    expired = security.create_access_token("42", "user", expires_delta=timedelta(seconds=-1))
    with pytest.raises(security.InvalidToken):
        security.decode_access_token(expired)


def test_rejects_tampered_and_alg_none_tokens():
    token = security.create_access_token("2", "user")
    header, payload, sig = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
    claims["role"] = "admin"
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    with pytest.raises(security.InvalidToken):
        security.decode_access_token(f"{header}.{forged}.{sig}")
    none_header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    with pytest.raises(security.InvalidToken):
        security.decode_access_token(f"{none_header}.{forged}.")
    with pytest.raises(security.InvalidToken):
        security.decode_access_token("garbage")


def test_register_does_not_store_or_return_plaintext():
    r = client.post("/auth/register", json={"email": "Ada@Example.com", "password": "correct-horse"})
    assert r.status_code == 201
    assert r.json() == {"id": 2, "email": "ada@example.com", "role": "user"}
    assert store.USERS[2]["password_hash"] != "correct-horse"
    assert client.post("/auth/register", json={"email": "ada@example.com", "password": "another-one"}).status_code == 409


def test_login_failures_are_indistinguishable():
    register_and_login()
    wrong_pw, no_user = login("ada@example.com", "nope-nope"), login("ghost@example.com", "nope-nope")
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()
    assert wrong_pw.headers["www-authenticate"] == "Bearer"


def test_me_requires_a_valid_bearer_token():
    token = register_and_login()
    assert client.get("/users/me", headers=auth(token)).json()["email"] == "ada@example.com"
    assert client.get("/users/me").status_code == 401
    assert client.get("/users/me", headers={"X-User-Id": "1"}).status_code == 401, "never trust identity headers"
    assert client.get("/users/me", headers=auth("garbage")).status_code == 401
    expired = security.create_access_token("2", "user", expires_delta=timedelta(seconds=-1))
    assert client.get("/users/me", headers=auth(expired)).status_code == 401


def test_deleted_user_token_is_rejected():
    token = register_and_login()
    del store.USERS[2]
    assert client.get("/users/me", headers=auth(token)).status_code == 401


def test_roles():
    user_token = register_and_login()
    assert client.get("/admin/users", headers=auth(user_token)).status_code == 403
    admin_token = login("admin@example.com", "adminpass123").json()["access_token"]
    r = client.get("/admin/users", headers=auth(admin_token))
    assert r.status_code == 200 and len(r.json()) == 2
    assert all("password_hash" not in u for u in r.json())


def test_docs_have_oauth2_scheme():
    schemes = client.get("/openapi.json").json()["components"]["securitySchemes"]
    assert any(s["type"] == "oauth2" for s in schemes.values())
