import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
ORIGIN = "http://localhost:5173"


@pytest.fixture
def client():
    main.OUTBOX.clear()
    main.STATE.update(started=False, stopped=False)
    with TestClient(main.app) as c:  # `with` runs lifespan startup/shutdown
        yield c


def test_lifespan_runs_startup_and_shutdown():
    main.STATE.update(started=False, stopped=False)
    with TestClient(main.app) as c:
        assert main.STATE == {"started": True, "stopped": False}
        assert c.get("/catalog").json()[0]["sku"] == "KB"
    assert main.STATE["stopped"] is True


def test_request_id_generated_and_propagated(client):
    r = client.get("/whoami")
    rid = r.headers.get("x-request-id")
    assert rid and len(rid) == 32
    assert r.json() == {"request_id": rid}
    r2 = client.get("/whoami", headers={"X-Request-ID": "abc123"})
    assert r2.headers["x-request-id"] == "abc123" and r2.json()["request_id"] == "abc123"


def test_process_time_header(client):
    value = client.get("/catalog").headers.get("x-process-time-ms")
    assert value is not None and float(value) >= 0


def test_cors_allows_frontend_only(client):
    preflight = {"Origin": ORIGIN, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
    r = client.options("/signup", headers=preflight)
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ORIGIN
    assert r.headers["access-control-allow-credentials"] == "true"

    evil = client.options("/signup", headers={**preflight, "Origin": "https://evil.example"})
    assert evil.headers.get("access-control-allow-origin") is None

    simple = client.get("/catalog", headers={"Origin": ORIGIN})
    assert simple.headers["access-control-allow-origin"] == ORIGIN
    assert "x-request-id" in simple.headers.get("access-control-expose-headers", "").lower()


def test_background_task(client):
    r = client.post("/signup", json={"email": "ada@example.com"})
    assert r.status_code == 202 and r.json() == {"status": "pending"}
    assert main.OUTBOX == ["ada@example.com"]  # TestClient waits for background tasks


def test_signup_uses_background_tasks(client, monkeypatch):
    seen = []
    monkeypatch.setattr(main, "send_welcome_email", lambda email: seen.append(email))
    import fastapi

    added = []
    original = fastapi.BackgroundTasks.add_task
    monkeypatch.setattr(fastapi.BackgroundTasks, "add_task", lambda self, fn, *a, **kw: (added.append(fn), original(self, fn, *a, **kw)))
    client.post("/signup", json={"email": "bob@example.com"})
    assert added, "use BackgroundTasks.add_task(...) instead of sending inline"


def test_gzip_large_responses_only(client):
    assert client.get("/big", headers={"Accept-Encoding": "gzip"}).headers.get("content-encoding") == "gzip"
    assert client.get("/catalog", headers={"Accept-Encoding": "gzip"}).headers.get("content-encoding") is None
