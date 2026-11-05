import hashlib
import json
import threading

import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture(autouse=True)
def reset():
    main.AVATARS.clear()


def upload(content: bytes, content_type="image/png", name="me.png"):
    return client.post("/avatars", files={"file": (name, content, content_type)})


def test_upload_ok():
    r = upload(PNG)
    assert r.status_code == 201, r.text
    assert r.json() == {"filename": "me.png", "content_type": "image/png", "size": len(PNG), "sha256": hashlib.sha256(PNG).hexdigest()}
    assert main.AVATARS[r.json()["sha256"]] == PNG


def test_upload_rejects_wrong_type_and_spoofed_content():
    assert upload(b"hello", "text/plain", "x.txt").status_code == 415
    assert upload(b"<script>alert(1)</script>", "image/png").status_code == 415, "check magic bytes, not just the header"


def test_upload_rejects_large_files():
    assert upload(PNG + b"\x00" * main.MAX_BYTES).status_code == 413
    assert main.AVATARS == {}


def test_csv_is_streamed():
    with client.stream("GET", "/export.csv") as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert r.headers["content-disposition"] == 'attachment; filename="books.csv"'
        chunks = list(r.iter_text())
    assert len(chunks) > 1, "send the CSV in many chunks (a generator), not one big string"
    lines = "".join(chunks).splitlines()
    assert lines[0] == "id,title,price_cents" and lines[1] == "1,Book 1,1001" and len(lines) == 1001


def test_sse_progress():
    with client.stream("GET", "/jobs/progress", params={"steps": 2}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    events = [e for e in body.split("\n\n") if e]
    assert [json.loads(e.removeprefix("data: ")) for e in events[:2]] == [{"step": 1, "of": 2}, {"step": 2, "of": 2}]
    assert events[2].startswith("event: done")


def run_with_timeout(fn, seconds=5):
    """A server that never sends would block receive_text() forever; fail instead of hanging."""
    outcome = {}

    def runner():
        try:
            fn()
        except BaseException as exc:  # noqa: BLE001
            outcome["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        pytest.fail("WebSocket test timed out waiting for a message: is the server broadcasting what the spec says?")
    if "error" in outcome:
        raise outcome["error"]


def test_websocket_rooms():
    run_with_timeout(websocket_scenario)


def websocket_scenario():
    # `with TestClient(...)` shares ONE event loop between all connections (like uvicorn does).
    # Without it, each websocket_connect gets its own loop thread and cross-connection broadcasts can race.
    with TestClient(main.app) as shared, shared.websocket_connect("/ws/rooms/python?name=ada") as ada:
        assert ada.receive_text() == "ada joined"
        with shared.websocket_connect("/ws/rooms/python?name=bob") as bob:
            assert ada.receive_text() == "bob joined"
            assert bob.receive_text() == "bob joined"
            with shared.websocket_connect("/ws/rooms/rust?name=eve") as eve:
                assert eve.receive_text() == "eve joined"
                bob.send_text("hi all")
                assert ada.receive_text() == "bob: hi all"
                assert bob.receive_text() == "bob: hi all"
                eve.send_text("anyone?")
                assert eve.receive_text() == "eve: anyone?"
        assert ada.receive_text() == "bob left"
