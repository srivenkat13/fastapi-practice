# Python + FastAPI interview question bank

> Short model answers for each question. Practise saying them **out loud** in about 60 seconds, then go deeper if asked. The ⭐ questions come up most often. The lesson tags (P3, F06, …) point to the hands-on version.

---

## 1. Python core

**⭐ What's the difference between a list and a tuple?** *(P2)*
A list is mutable. A tuple is immutable and hashable if its items are, so it can be a dict key or set member. Use tuples for fixed-shape records and lists for collections that grow.

**⭐ Mutable default arguments: what's the bug?** *(P3)*
Defaults are evaluated once, when the `def` runs, so `def f(x=[])` shares one list across calls. Use `None` and create the list inside the function.

**`is` vs `==`?** *(P1)*
`==` compares values (`__eq__`). `is` compares identity. Use `is` only for singletons such as `None`.

**What's falsy in Python?**
`None`, `False`, `0`, `0.0`, `""`, and empty containers. Watch out for `if not x` when `0` is a valid value.

**⭐ Explain decorators. Write one with arguments.** *(P3)*
A decorator is a function that takes a function and returns a replacement: `@d` means `f = d(f)`. A decorator with arguments is a factory: `retry(3)(f)`, so there are three levels of functions. Use `functools.wraps` to keep the name, docstring and signature (FastAPI inspects signatures).

**What are `*args` and `**kwargs`?**
They collect extra positional arguments into a tuple and keyword arguments into a dict. In a call, `*`/`**` unpack. A bare `*` in a signature makes the following parameters keyword-only.

**⭐ Generators: what and why?** *(P7)*
A function with `yield` produces values lazily, one at a time. It uses O(1) memory, supports pipelines and early exit, and is single-use. A generator expression is `(x for x in xs)`. FastAPI's yield dependencies and StreamingResponse are built on them.

**What does a context manager do? How do you write one?** *(P4)*
`with` guarantees setup and teardown: `__enter__`/`__exit__`, or `@contextmanager` around a `yield` inside `try/finally`. Used for files, locks, sessions and transactions.

**dataclass vs Pydantic model vs NamedTuple?** *(P4, F03)*
A dataclass is boilerplate-free and doesn't validate. Pydantic validates and coerces at runtime and serializes, so use it at the boundaries. A NamedTuple is an immutable tuple with names.

**⭐ How does Python manage memory?**
Reference counting frees objects immediately when the count hits zero. A cyclic garbage collector handles reference cycles. Everything is an object on the heap, and names are references.

**What is the GIL?** *(P8)*
The Global Interpreter Lock lets only one thread execute Python bytecode at a time. I/O and many C extensions release it. So threads help I/O-bound work, and CPU-bound work needs processes. Python 3.13+ has an optional free-threaded build.

**`@staticmethod` vs `@classmethod`?**
A classmethod receives `cls` (use it for alternative constructors, and it works with subclasses). A staticmethod is a plain function namespaced on the class.

**What are dunder methods? Give examples.**
Methods that hook into syntax: `__init__`, `__repr__`, `__eq__`/`__hash__`, `__len__`, `__iter__`, `__getitem__`, `__enter__`/`__exit__`, `__call__`.

**How do imports work? How do you fix a circular import?** *(P5)*
Modules run once and are cached in `sys.modules`, and they're found via `sys.path`. To fix a circular import, move shared code into a third module, import inside the function, or use `TYPE_CHECKING`-only imports for type hints.

**Shallow vs deep copy?**
A shallow copy (`copy()`, `list(x)`, `{**d}`) copies the outer container but shares the nested objects. `copy.deepcopy` copies recursively.

**Are type hints enforced?** *(P6)*
No, not by Python. Static checkers (mypy, pyright) use them, and runtime libraries (Pydantic, FastAPI) read them to validate.

**`Protocol` vs ABC?** *(P6)*
A Protocol is structural, like TS interfaces: anything with the right methods matches. An ABC is nominal: you must inherit, and it can enforce abstract methods.

**How are dicts implemented? Complexity?**
Hash tables. Get, set and `in` are O(1) on average. Insertion order is preserved since 3.7.

**`venv`, pip, pyproject: how do you manage dependencies?** *(P5)*
A per-project virtualenv, dependencies declared in `pyproject.toml`, locked for reproducible builds (uv/poetry lock or pinned requirements), and Python versions managed with pyenv or `uv python`.

---

## 2. Async & concurrency

**⭐ How does asyncio work?** *(P8)*
A single-threaded event loop runs coroutines. At each `await` of I/O, control returns to the loop, which runs other ready tasks. It's cooperative multitasking, so anything that blocks stalls everyone.

**⭐ `async def` vs `def` endpoints in FastAPI?** *(F12)*
`async def` runs on the event loop, so everything inside must be awaitable or non-blocking. `def` runs in a threadpool, which is safe for blocking libraries. The trap is a blocking call inside `async def`.

**gather vs TaskGroup vs create_task?**
`gather` runs awaitables concurrently (`return_exceptions=True` is like allSettled). `TaskGroup` (3.11+) gives structured concurrency: a failure cancels the siblings and raises an ExceptionGroup. `create_task` schedules a task in the background, and you need to keep a reference to it.

**How do you limit concurrency or add timeouts?**
`asyncio.Semaphore(n)` for concurrency, and `async with asyncio.timeout(s)` or `wait_for` for timeouts.

**Threads vs processes vs async?**
Async for many concurrent I/O waits, threads for blocking I/O libraries, processes for CPU-bound work.

**What is a ContextVar and why does it matter in async?** *(R3)*
Per-task context, the async-safe version of a thread-local. Use it for request IDs, the current user in logging, and tracing.

---

## 3. FastAPI

**⭐ What is FastAPI built on, and why is it fast?** *(F01)*
Starlette (ASGI) plus Pydantic (with a Rust core) plus type hints. You get async I/O, automatic validation, serialization and OpenAPI. It's also fast to develop with.

**⭐ ASGI vs WSGI?** *(F01, R1)*
ASGI is async-native and supports WebSockets, streaming and many concurrent connections per process. WSGI is synchronous, one request per worker thread.

**⭐ How does FastAPI decide where a parameter comes from?** *(F02, P6)*
A name that appears in the path template is a path param. A Pydantic model is the body. A simple type is a query param. `Annotated[..., Header()/Cookie()/Body()/Depends()]` makes it explicit.

**⭐ Explain dependency injection in FastAPI.** *(F06)*
`Depends(callable)`: FastAPI resolves the callable's own parameters recursively, caches the result per request, and runs teardown for `yield` dependencies. Use it for DB sessions, auth, pagination, settings and clients. Tests use `dependency_overrides`.

**How do yield dependencies work? When does cleanup run?** *(F06)*
The code before `yield` is setup, the yielded value is injected, and the code after `yield` runs after the response (or right after the endpoint with `scope="function"`). Endpoint exceptions are re-raised at the `yield`.

**⭐ What's `response_model` for?** *(F04)*
It filters the output to the declared fields (an allow-list, which stops sensitive fields leaking), validates the output, and documents the response schema.

**How do you return a custom status code or headers?** *(F04)*
`status_code=` on the decorator, a `response: Response` parameter to set headers, or return a `JSONResponse`, `Response` or `StreamingResponse` directly.

**How do you handle errors consistently?** *(F05)*
Domain exceptions in services, `@app.exception_handler` mapping them to one envelope, overridden `RequestValidationError` and Starlette `HTTPException` handlers, and a generic 500 that leaks nothing.

**Middleware vs dependencies?** *(F13)*
Middleware wraps every request and is cross-cutting (timing, request IDs, CORS, GZip). Dependencies are per-route, typed, composable and overridable, so auth belongs there.

**What is lifespan?** *(F13)*
An async context manager that runs startup before `yield` and shutdown after it, once per worker. Use it for DB pools, HTTP clients and ML models. It replaces the deprecated `on_event`.

**BackgroundTasks vs a task queue?** *(F13)*
BackgroundTasks run in-process after the response, best-effort, and are lost on crash. Use a queue (Celery, RQ, Arq, SQS) for durability, retries, scheduling and scaling.

**How do you structure a large FastAPI project?** *(F07)*
Routers per feature, a services layer, separate schemas and models, shared deps, config via pydantic-settings, and an app factory.

**How do you version APIs in FastAPI?** *(F07, F15)*
`include_router(router, prefix="/v1")`, run v2 side by side, and send Deprecation and Sunset headers.

**How does FastAPI generate docs? How do frontend teams use them?** *(F01, F15)*
From routes, models and type hints into OpenAPI 3.1 at `/openapi.json`, served as Swagger UI at `/docs`. Teams generate TS clients from it (openapi-typescript, orval). Use clean `operationId`s.

**WebSockets / SSE / streaming in FastAPI?** *(F14)*
`@app.websocket` for two-way, `StreamingResponse` with `text/event-stream` for SSE, and a generator for large downloads. Scale WebSockets with Redis pub/sub.

---

## 4. Pydantic

**⭐ How does validation work in Pydantic v2?** *(F03)*
Type hints plus `Field` constraints, then `field_validator` and `model_validator`. The default lax mode coerces (`"5"` → `5`), and strict mode doesn't. Errors are collected and returned as a 422 in FastAPI.

**v1 → v2 changes?**
A Rust core (much faster), `model_dump`/`model_validate`/`model_config`, `field_validator` replacing `validator`, and `from_attributes` replacing `orm_mode`.

**How do you implement PATCH?** *(F03, F09)*
All fields optional, then `model_dump(exclude_unset=True)` to apply only the fields that were sent.

**How do you reject unknown fields?**
`model_config = ConfigDict(extra="forbid")`. It stops typos and mass assignment.

**Settings management?** *(F07, R4)*
`pydantic-settings` `BaseSettings`: env vars plus `.env`, typed, validated at boot, `SecretStr` for secrets, cached with `lru_cache`.

---

## 5. Databases & SQLAlchemy

**⭐ What's the N+1 problem? How do you fix it?** *(F08)*
One query for the list and one more per row for a relation. Fix it with `selectinload` or `joinedload`, and find it with query logging or query-count tests.

**How do you manage DB sessions in FastAPI?** *(F08)*
One session per request through a yield dependency, always closed, with `expire_on_commit=False`. Never a global session.

**How do you do migrations?** *(F08)*
Alembic `revision --autogenerate`, review the file, run `upgrade head` in the pipeline. Keep changes backwards-compatible (expand, migrate, contract).

**Offset vs cursor pagination?** *(F09, D2)*
Offset is simple and supports random access, but it's slow on deep pages and unstable under writes. Keyset/cursor pagination is O(1) with an index and stable, but you can only go next or prev.

**⭐ How do you prevent lost updates or race conditions?** *(F15, D4)*
Optimistic locking (a version column or ETag/If-Match), pessimistic locking (`SELECT ... FOR UPDATE`), atomic SQL (`UPDATE ... SET x = x + 1 WHERE ...`), or unique constraints.

**Transactions and isolation levels?**
ACID. Read committed is Postgres's default. Repeatable read and serializable prevent more anomalies (non-repeatable reads, phantoms, write skew) at the cost of retries.

**Indexes: when and which?**
On filter, join and sort columns. Composite index order matters (equality columns first, then range or sort). Use EXPLAIN ANALYZE. Indexes have a write cost.

**Sync vs async SQLAlchemy?** *(F12)*
Async with asyncpg gives higher concurrency, but there's no lazy loading (eager-load everything). Sync in `def` endpoints is fine at moderate scale.

---

## 6. Auth & security

**⭐ How do you store passwords?** *(F10)*
Argon2id or bcrypt: slow, salted, with tunable cost. Constant-time verify, and never plaintext or a fast hash.

**⭐ JWT vs sessions?** *(F10)*
JWTs are stateless and scale easily but are hard to revoke, so keep them short-lived with refresh tokens. Server sessions are revocable but need a lookup (Redis).

**JWT pitfalls?** *(F10)*
`alg:none` and algorithm confusion (pin `algorithms=[...]`), weak secrets, missing `exp` validation, sensitive data in the payload (it's only base64), and no revocation.

**401 vs 403? And when 404 instead?** *(F10, C1)*
401 means unauthenticated and 403 means forbidden. Return 404 for resources the user shouldn't know exist.

**Where should tokens live in a React SPA?** *(F10)*
An access token in memory plus a refresh token in an httpOnly, Secure, SameSite cookie. Avoid localStorage (XSS). Cookies need CSRF protection.

**⭐ Explain CORS.** *(F13)*
A browser-enforced same-origin policy. The server allow-lists origins, and non-simple requests are preflighted with OPTIONS. You can't use `*` with credentials. CORS doesn't protect the server itself.

**OWASP API top risks?**
Broken object-level authorization (most common), broken auth, excessive data exposure, missing rate limits, mass assignment, injection, and misconfiguration. Each one maps to a lesson here.

**How do you prevent SQL injection?** *(F09)*
Bound parameters (ORM or `text()` with params), and never string-format SQL. Whitelist identifiers such as sort columns.

---

## 7. REST & HTTP design

**⭐ Idempotency: which methods, and how do you make POST idempotent?** *(F15, D4)*
GET, PUT and DELETE are idempotent. For POST, use an Idempotency-Key header with a stored response, a request fingerprint, a TTL, and a lock for concurrent duplicates.

**PUT vs PATCH?** *(F09)*
PUT is a full replacement and idempotent. PATCH is partial.

**Status codes you'd use for…** *(F04, F09)*
Create 201 + Location, async job 202, delete 204, validation 422/400, conflict 409, precondition 412/428, rate limit 429, upstream failure 502/503/504.

**⭐ Design a rate limiter.** *(F15, D1)*
A token bucket or sliding window, Redis atomic operations shared across instances, per user or API key, 429 + Retry-After, and the tightest limits on auth endpoints.

**How do you cache API responses?** *(R2, F15)*
HTTP headers (Cache-Control, ETag, Vary) for browsers and CDNs, plus Redis cache-aside with TTL and invalidation on write. Prevent stampedes with single-flight.

**How do you design list endpoints?** *(F09)*
An envelope, filters, a whitelisted sort with a tie-breaker, limits with a maximum, cursor or offset pagination, and a consistent total.

---

## 8. Testing

**⭐ How do you test FastAPI apps?** *(F11)*
pytest + TestClient, fixtures in conftest, `dependency_overrides` for DB, auth and clock, and a real DB per test (transaction rollback). httpx AsyncClient + ASGITransport for async tests.

**How do you test time, randomness or external APIs?** *(F11, F12)*
Inject them as dependencies and override them in tests. respx/httpx mocks for HTTP, and freezegun/time-machine for time.

**Is code coverage enough?** *(F11)*
No. Mutation testing checks whether tests actually catch bugs. Test boundaries and auth paths.

---

## 9. Performance, scaling & ops

**⭐ A FastAPI endpoint is slow under load. How do you investigate?** *(F12, R3)*
Check metrics first (p99, error rate, saturation), then traces to find where the time goes. Usual causes: blocking calls in async endpoints, an exhausted DB pool or threadpool, N+1 queries, missing indexes, missing upstream timeouts, or CPU-bound work. Fix the cause, then add caching.

**How do you scale a FastAPI service?** *(R4)*
Stateless app instances (workers ≈ cores, or 1 per pod with horizontal scaling), state in Postgres and Redis, connection pooling (PgBouncer), caching, async I/O, and queues for slow work.

**How do you deploy?** *(R4)*
A container (slim, non-root), uvicorn workers behind a load balancer with TLS, config from env and a secret manager, health probes, migrations before rollout, rolling or blue-green deploys, graceful shutdown.

**Liveness vs readiness?** *(R3)*
Liveness means restart if the process is stuck (no dependency checks). Readiness means stop routing traffic while dependencies are down.

**How do you trace a request across services?** *(R3)*
Request or trace IDs (OpenTelemetry `traceparent`) propagated in headers and logged in structured JSON.

---

## 10. Framework judgement

**⭐ FastAPI vs Flask vs Django: when do you pick each?** *(R1, framework-comparison.md)*
FastAPI for API-first, typed, async services. Django for full-stack products needing an admin, auth and ORM batteries. Flask for small or legacy apps and server-rendered pages with a flexible plugin ecosystem.

**Why Python for backend vs Node?**
Python has the data and ML ecosystem, readability and mature libraries. Node shares a language with the frontend and has strong single-threaded async I/O. FastAPI closes much of the async gap. Pick based on the team and the domain.

**What would you add to make this service production-ready?** *(C1)*
Migrations, observability (logs, metrics, traces), rate limiting, timeouts and retries, health checks, CI with tests, linting and type checks, security headers, secrets management, backups, and runbooks.
