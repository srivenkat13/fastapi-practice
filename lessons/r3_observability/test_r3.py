import json
import logging
import sys

import pytest
from fastapi.testclient import TestClient

from support import target

obs = target(__file__, "observability")
main = target(__file__, "main")
client = TestClient(main.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset():
    main.app.dependency_overrides.clear()


def records(caplog, logger):
    return [r for r in caplog.records if r.name == logger]


def test_json_formatter():
    record = logging.LogRecord("app.orders", logging.INFO, __file__, 1, "order %s viewed", (7,), None)
    record.order_id = 7
    record.request_id = "rid-1"
    line = obs.JsonFormatter().format(record)
    data = json.loads(line)
    assert data["message"] == "order 7 viewed" and data["level"] == "INFO" and data["logger"] == "app.orders"
    assert data["request_id"] == "rid-1" and data["order_id"] == 7
    assert data["ts"].endswith("+00:00")
    assert "\n" not in line


def test_json_formatter_includes_exceptions():
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord("app", logging.ERROR, __file__, 1, "failed", None, sys.exc_info())
    data = json.loads(obs.JsonFormatter().format(record))
    assert "ValueError: boom" in data["exception"]


def test_configure_logging_is_idempotent():
    logger = obs.configure_logging()
    obs.configure_logging()
    assert len(logger.handlers) == 1 and isinstance(logger.handlers[0].formatter, obs.JsonFormatter)
    assert sum(isinstance(f, obs.RequestIdFilter) for f in logger.filters) == 1


def test_request_id_flows_into_logs(caplog):
    caplog.set_level(logging.INFO, logger="app")
    r = client.get("/orders/7", headers={"X-Request-ID": "trace-123"})
    assert r.headers["x-request-id"] == "trace-123"
    [viewed] = records(caplog, "app.orders")
    assert viewed.getMessage() == "order viewed" and viewed.order_id == 7 and viewed.request_id == "trace-123"
    [access] = records(caplog, "app.access")
    assert (access.method, access.path, access.status, access.request_id) == ("GET", "/orders/7", 200, "trace-123")
    assert access.duration_ms >= 0


def test_context_is_reset_between_requests(caplog):
    caplog.set_level(logging.INFO, logger="app")
    client.get("/orders/1", headers={"X-Request-ID": "first"})
    assert obs.request_id_var.get() == "-"
    second = client.get("/orders/2")
    assert len(second.headers["x-request-id"]) == 32


def test_500s_are_logged_and_correlated(caplog):
    caplog.set_level(logging.INFO, logger="app")
    r = client.get("/orders/13", headers={"X-Request-ID": "bad-1"})
    assert r.status_code == 500
    assert r.json() == {"error": "internal_error", "request_id": "bad-1"}
    assert "corrupted" not in r.text
    errors = [rec for rec in caplog.records if rec.levelno >= logging.ERROR]
    assert errors and errors[0].exc_info and errors[0].request_id == "bad-1"
    assert any(a.status == 500 for a in records(caplog, "app.access"))


def test_404_access_log(caplog):
    caplog.set_level(logging.INFO, logger="app")
    client.get("/orders/500")
    [access] = records(caplog, "app.access")
    assert access.status == 404


def test_health_and_readiness():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ok", "checks": {"db": "ok", "cache": "ok"}}

    def broken():
        raise ConnectionError("redis down")

    main.app.dependency_overrides[main.get_checks] = lambda: {"db": lambda: True, "cache": broken}
    r = client.get("/ready")
    assert r.status_code == 503 and r.json() == {"status": "unavailable", "checks": {"db": "ok", "cache": "fail"}}
    assert client.get("/health").status_code == 200, "liveness must not depend on downstream services"
