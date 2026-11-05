import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)


def module(name):
    return target(__file__, name)


@pytest.fixture(autouse=True)
def reset():
    main.app.dependency_overrides.clear()
    yield
    getattr(module("config"), "get_settings", None) and module("config").get_settings.cache_clear()


def test_routers_exist():
    for name, prefix, tag in (("books", "/books", "books"), ("authors", "/authors", "authors"), ("meta", "", "meta")):
        router = getattr(module(f"routers.{name}"), "router", None)
        assert isinstance(router, APIRouter), f"routers/{name}.py must define `router = APIRouter(...)`"
        assert router.prefix == prefix and router.tags == [tag]


def test_versioned_paths():
    assert [b["id"] for b in client.get("/api/v1/books").json()] == [1, 2, 3]
    assert client.get("/api/v1/books/2").json()["title"] == "Dune"
    assert client.get("/api/v1/books/9").status_code == 404
    assert len(client.get("/api/v1/authors/2/books").json()) == 2
    assert client.get("/books").status_code == 404, "unversioned paths should be gone"


def test_settings_from_env(monkeypatch):
    config = module("config")
    monkeypatch.setenv("BOOKSHELF_APP_NAME", "From Env")
    monkeypatch.setenv("BOOKSHELF_DEBUG", "true")
    config.get_settings.cache_clear()
    s = config.get_settings()
    assert s.app_name == "From Env" and s.debug is True
    assert config.get_settings() is s, "get_settings should be cached (functools.lru_cache)"


def test_settings_validate_types(monkeypatch):
    config = module("config")
    assert hasattr(config, "Settings"), "config.py must define Settings"
    from pydantic import ValidationError

    monkeypatch.setenv("BOOKSHELF_MAX_PAGE_SIZE", "lots")
    with pytest.raises(ValidationError):
        config.Settings()


def test_info_uses_settings_dependency():
    config = module("config")
    main.app.dependency_overrides[config.get_settings] = lambda: config.Settings(app_name="Overridden", debug=True)
    assert client.get("/api/v1/info").json() == {"app_name": "Overridden", "debug": True}


def test_main_has_no_endpoints_of_its_own():
    own = [r for r in main.app.routes if getattr(r, "endpoint", None) and r.endpoint.__module__ == main.__name__]
    assert own == [], "keep endpoint functions in routers/, main.py only assembles the app"
