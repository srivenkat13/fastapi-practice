# F12 · Async in practice: `def` vs `async def`, concurrency, timeouts, async DB

> FastAPI lets you write endpoints as `def` **or** `async def`, and choosing wrong can quietly reduce throughput by 10–100×. This lesson covers the rules, plus the patterns real services use: one shared HTTP client, concurrent fan-out, timeouts with graceful degradation, and an async ORM.

## 🧠 Concepts

### The rule
| Your endpoint does... | Write | Why |
|---|---|---|
| `await`-able I/O (httpx.AsyncClient, asyncpg, async SQLAlchemy, aioredis) | `async def` | runs on the event loop, so it's cheap and highly concurrent |
| blocking I/O (requests, a sync DB driver, boto3, sync SDKs) | `def` | FastAPI runs it in a **threadpool** (40 threads by default) |
| both | `async def` + `await asyncio.to_thread(blocking_fn)` | keeps the loop free |
| heavy CPU (images, ML, big JSON) | offload to a process pool or task queue (Celery/RQ/Arq) | the GIL blocks everything |

**The worst case is `async def` plus a blocking call**: `time.sleep`, `requests.get` or a sync DB query freezes the loop for **every** request on that worker. Dependencies follow the same `def` / `async def` rule.

### One shared HTTP client (created in lifespan)
```python
@asynccontextmanager
async def lifespan(app):
    async with httpx.AsyncClient(base_url=..., timeout=5) as client:
        app.state.http = client      # connection pooling + keep-alive
        yield
```
Creating a new client per request throws away connection reuse and costs TLS handshakes.

### Fan-out, timeouts, degradation
```python
profile, orders = await asyncio.gather(http.get(...), http.get(...))   # concurrent
async with asyncio.timeout(0.3): ...                                   # bound the wait
except TimeoutError: return {"quote": None, "degraded": True}          # partial response > hung request
```
Production setups add retries with exponential backoff and jitter (`tenacity`, or an httpx transport with retries), circuit breakers, and bulkheads (a semaphore per upstream).

### Async SQLAlchemy
```python
engine = create_async_engine("postgresql+asyncpg://...")      # SQLite: "sqlite+aiosqlite://"
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
async with SessionLocal() as session:
    session.add(obj)                                          # sync: stages only
    await session.commit()                                    # I/O → await
    rows = await session.scalars(select(Note))
```
⚠️ **No lazy loading in async.** Touching an unloaded relationship raises `MissingGreenlet`. Always eager-load (`selectinload`), or use `AsyncAttrs` + `await obj.awaitable_attrs.rel`.

### Testing async code
`httpx.AsyncClient(transport=ASGITransport(app=app))` runs your app in the **test's** event loop. That's how these tests catch loop-blocking: three concurrent `/report` requests take 0.6s if blocked, and 0.2s if not.

## 🏋️ Exercise
In `exercise/main.py`:
1. `/dashboard/{id}`: make the three upstream calls concurrent.
2. `/report`: stop blocking the loop (make it `def`, or use `asyncio.to_thread`).
3. `/quote`: add a 0.3s timeout that returns `{"quote": None, "degraded": True}`.
4. `/notes`: implement with the async session.

```bash
python check.py f12
# run it for real: two terminals
python -m uvicorn lessons.f12_async.upstream:app --port 9000
python run.py f12
```

## 💼 Interview angle
- *"When do you use `async def` vs `def` in FastAPI?"*: async when everything inside is awaitable. Use def for blocking libraries (threadpool). Never block inside async.
- *"Your FastAPI service's p99 latency jumps under load, but CPU is low. Why?"*: likely a blocking call in an async endpoint (the loop is stalled), an exhausted threadpool or DB pool, or missing timeouts on upstream calls.
- *"How do you call several microservices efficiently?"*: a shared client, `gather`/TaskGroup, a timeout per call, retries with backoff, and partial responses.
- *"Is async always faster?"*: no. It improves **concurrency** for I/O-bound work, not raw speed. CPU-bound work gets nothing from it, and sync code in a threadpool is fine at moderate load.
- *"What's the GIL's impact on FastAPI?"*: threads don't run Python in parallel, so scale CPU across **processes** (multiple uvicorn workers, more pods).
