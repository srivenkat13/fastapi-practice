"""Async tests: the app, the fake upstream and the DB all share ONE event loop, so timing reveals blocking."""
import asyncio
import time

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from lessons.f12_async import upstream
from support import target

database = target(__file__, "database")
main = target(__file__, "main")
pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    upstream_client = httpx.AsyncClient(transport=httpx.ASGITransport(app=upstream.app), base_url="http://upstream")
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    await database.create_tables(engine)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def session_override():
        async with Session() as s:
            yield s

    main.app.dependency_overrides[main.get_http] = lambda: upstream_client
    main.app.dependency_overrides[database.get_async_session] = session_override
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as c:
        yield c
    main.app.dependency_overrides.clear()
    await upstream_client.aclose()
    await engine.dispose()


async def test_dashboard_calls_upstream_concurrently(client):
    start = time.perf_counter()
    r = await client.get("/dashboard/7")
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert r.json()["profile"]["name"] == "User 7" and r.json()["recommendations"][0] == "Fluent Python"
    assert elapsed < 0.25, f"took {elapsed:.2f}s: the three upstream calls should run concurrently (asyncio.gather)"


async def test_blocking_work_does_not_freeze_the_loop(client):
    start = time.perf_counter()
    responses = await asyncio.gather(*(client.get("/report") for _ in range(3)))
    elapsed = time.perf_counter() - start
    assert all(r.json() == {"report": "ready"} for r in responses)
    assert elapsed < 0.45, f"3 concurrent reports took {elapsed:.2f}s: time.sleep inside `async def` blocks the event loop"


async def test_quote_times_out_gracefully(client):
    start = time.perf_counter()
    r = await client.get("/quote")
    assert r.status_code == 200
    assert r.json() == {"quote": None, "degraded": True}
    assert time.perf_counter() - start < 0.8


async def test_async_db(client):
    assert (await client.post("/notes", json={"text": "first"})).status_code == 201
    await client.post("/notes", json={"text": "second"})
    assert (await client.get("/notes")).json() == [{"id": 1, "text": "first"}, {"id": 2, "text": "second"}]
