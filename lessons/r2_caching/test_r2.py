import asyncio

import httpx
import pytest

from support import target

cache_mod = target(__file__, "cache")
db = target(__file__, "db")
main = target(__file__, "main")


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def cache(clock):
    return cache_mod.InMemoryCache(clock=clock)


@pytest.fixture
async def client(cache):
    db.CALLS.update(get_product=0, list_products=0)
    db.PRODUCTS.clear()
    db.PRODUCTS.update({1: {"id": 1, "name": "Keyboard", "price_cents": 12999}, 2: {"id": 2, "name": "Mouse", "price_cents": 4999}})
    main.app.dependency_overrides[main.get_cache] = lambda: cache
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://t") as c:
        yield c
    main.app.dependency_overrides.clear()


def test_ttl_and_delete(cache, clock):
    assert cache.get("k") is cache_mod.MISSING
    cache.set("k", None, ttl=10)
    assert cache.get("k") is None, "None is a valid cached value (negative caching)"
    cache.set("k", "v", ttl=10)
    clock.now += 9.9
    assert cache.get("k") == "v"
    clock.now += 0.2
    assert cache.get("k") is cache_mod.MISSING
    cache.set("k", "v", ttl=10)
    cache.delete("k")
    cache.delete("never-set")
    assert cache.get("k") is cache_mod.MISSING


@pytest.mark.anyio
async def test_cache_aside_hit_miss_and_expiry(client, clock):
    r1 = await client.get("/products/1")
    r2 = await client.get("/products/1")
    assert (r1.headers["x-cache"], r2.headers["x-cache"]) == ("MISS", "HIT")
    assert r1.json() == r2.json() and db.CALLS["get_product"] == 1
    clock.now += 61
    assert (await client.get("/products/1")).headers["x-cache"] == "MISS"
    assert db.CALLS["get_product"] == 2


@pytest.mark.anyio
async def test_negative_caching(client, clock):
    assert (await client.get("/products/99")).status_code == 404
    assert (await client.get("/products/99")).status_code == 404
    assert db.CALLS["get_product"] == 1, "cache 'not found' briefly to protect the DB from repeated misses"
    clock.now += 11
    await client.get("/products/99")
    assert db.CALLS["get_product"] == 2, "negative entries need a short TTL"


@pytest.mark.anyio
async def test_write_invalidates(client):
    await client.get("/products/1")
    await client.put("/products/1", json={"name": "Keyboard Pro", "price_cents": 14999})
    r = await client.get("/products/1")
    assert r.headers["x-cache"] == "MISS" and r.json()["name"] == "Keyboard Pro"


@pytest.mark.anyio
async def test_single_flight_prevents_stampede(client):
    responses = await asyncio.gather(*(client.get("/products/2") for _ in range(5)))
    assert all(r.json()["name"] == "Mouse" for r in responses)
    assert db.CALLS["get_product"] == 1, f"{db.CALLS['get_product']} DB calls for 5 concurrent misses: add single-flight locking"


@pytest.mark.anyio
async def test_http_cache_headers(client):
    assert (await client.get("/catalog")).headers["cache-control"] == "public, max-age=60, stale-while-revalidate=30"
    assert (await client.get("/me/cart")).headers["cache-control"] == "private, no-store"


def test_get_cache_returns_a_singleton():
    main.app.dependency_overrides.clear()
    assert main.get_cache() is main.get_cache()
    assert isinstance(main.get_cache(), cache_mod.InMemoryCache)
