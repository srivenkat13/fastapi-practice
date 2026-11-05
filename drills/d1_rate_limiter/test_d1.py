import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)
KEY_A, KEY_B = {"X-API-Key": "a"}, {"X-API-Key": "b"}


@pytest.fixture(autouse=True)
def clock():
    now = [100.0]
    for limiter in (main.search_limiter, main.export_limiter):
        getattr(limiter, "hits", {}).clear()
    main.app.dependency_overrides[main.get_clock] = lambda: now[0]
    yield now
    main.app.dependency_overrides.clear()


def test_requires_key():
    assert client.get("/search").status_code == 401


def test_limit_and_headers():
    for remaining in ("2", "1", "0"):
        r = client.get("/search", headers=KEY_A)
        assert r.status_code == 200 and r.headers["x-ratelimit-remaining"] == remaining
    assert r.headers["x-ratelimit-limit"] == "3"
    blocked = client.get("/search", headers=KEY_A)
    assert blocked.status_code == 429 and blocked.headers["retry-after"] == "10"


def test_sliding_window(clock):
    client.get("/search", headers=KEY_A)  # t=100
    clock[0] = 105
    client.get("/search", headers=KEY_A)  # t=105
    client.get("/search", headers=KEY_A)  # t=105
    clock[0] = 109
    r = client.get("/search", headers=KEY_A)
    assert r.status_code == 429 and r.headers["retry-after"] == "1"
    clock[0] = 110.5  # the t=100 hit has left the window, the t=105 hits have not
    assert client.get("/search", headers=KEY_A).status_code == 200
    assert client.get("/search", headers=KEY_A).status_code == 429, "a fixed window would wrongly allow this"


def test_keys_and_limiters_are_independent():
    for _ in range(3):
        client.get("/search", headers=KEY_A)
    assert client.get("/search", headers=KEY_A).status_code == 429
    assert client.get("/search", headers=KEY_B).status_code == 200
    assert client.post("/export", headers=KEY_A).status_code == 200, "export has its own bucket"
    assert client.post("/export", headers=KEY_A).status_code == 429


def test_health_is_not_limited():
    for _ in range(10):
        assert client.get("/health").status_code == 200
