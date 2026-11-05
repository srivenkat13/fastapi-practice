import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from support import target, using_solutions

settings_mod = target(__file__, "settings")
app_mod = target(__file__, "app")
HERE = Path(__file__).parent / ("solution" if using_solutions() else "exercise")
GOOD_SECRET = "x" * 40


def make(**kw):
    return TestClient(app_mod.create_app(settings_mod.Settings(**kw)))


def test_settings_defaults_and_env(monkeypatch):
    s = settings_mod.Settings()
    assert s.environment == "dev" and s.secret_key is None and s.allowed_hosts == ["*"] and not s.is_prod
    monkeypatch.setenv("R4_ENVIRONMENT", "test")
    monkeypatch.setenv("R4_ALLOWED_HOSTS", '["api.example.com"]')
    s = settings_mod.Settings()
    assert s.environment == "test" and s.allowed_hosts == ["api.example.com"]
    with pytest.raises(ValidationError):
        settings_mod.Settings(environment="staging")


def test_secret_is_hidden():
    s = settings_mod.Settings(secret_key=GOOD_SECRET)
    assert GOOD_SECRET not in repr(s) and GOOD_SECRET not in str(s.model_dump())
    assert s.secret_key.get_secret_value() == GOOD_SECRET


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"secret_key": "short", "allowed_hosts": ["api.example.com"]},
        {"secret_key": GOOD_SECRET},  # allowed_hosts still "*"
    ],
)
def test_prod_fails_fast_when_misconfigured(kwargs):
    with pytest.raises(ValidationError):
        settings_mod.Settings(environment="prod", **kwargs)


def test_dev_app():
    c = make()
    assert c.get("/docs").status_code == 200
    r = c.get("/version")
    assert r.json() == {"version": "dev", "environment": "dev"}
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert "strict-transport-security" not in r.headers


def test_prod_app():
    c = TestClient(
        app_mod.create_app(settings_mod.Settings(environment="prod", secret_key=GOOD_SECRET, allowed_hosts=["api.example.com"], version="1.4.2")),
        base_url="https://api.example.com",
    )
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert c.get(path).status_code == 404, f"{path} should be disabled in prod"
    r = c.get("/version")
    assert r.json() == {"version": "1.4.2", "environment": "prod"}
    assert r.headers["strict-transport-security"].startswith("max-age=")
    assert c.get("/health", headers={"host": "evil.example"}).status_code == 400


def dockerfile() -> str:
    return (HERE / "Dockerfile").read_text()


def test_dockerfile_runs_as_non_root():
    users = re.findall(r"^USER\s+(\S+)", dockerfile(), re.M)
    assert users and users[-1] not in ("root", "0")


def test_dockerfile_production_command():
    text = dockerfile()
    assert "--reload" not in text, "--reload is for development only"
    assert "0.0.0.0" in text, "bind 0.0.0.0 or the server is unreachable from outside the container"
    assert re.search(r"--workers", text), "run several worker processes"


def test_dockerfile_layer_caching_and_size():
    text = dockerfile()
    assert "--no-cache-dir" in text
    assert re.search(r"^FROM python:3\.\d+-slim", text, re.M), "use a slim base image"
    req, src = text.find("COPY requirements.txt"), text.find("COPY . .")
    assert 0 <= req < src, "copy requirements.txt and install BEFORE copying the source (layer caching)"
    assert "HEALTHCHECK" in text


def test_dockerignore():
    entries = {line.strip() for line in (HERE / ".dockerignore").read_text().splitlines()}
    for must in (".venv", ".env", ".git"):
        assert must in entries, f"{must} must not be copied into the image"
    assert any("__pycache__" in e for e in entries)
