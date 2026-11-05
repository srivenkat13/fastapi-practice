# F13 · Middleware, CORS, lifespan, background tasks

> These are the cross-cutting pieces that wrap every request (middleware), the browser rule every React developer has run into (CORS), app startup and shutdown (lifespan), and fire-and-forget work after the response (background tasks).

## 🧠 Concepts

### Middleware = code around every request
```python
@app.middleware("http")
async def timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)          # the rest of the stack + your endpoint
    response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.2f}"
    return response

app.add_middleware(GZipMiddleware, minimum_size=1000)
```
- **Order**: the last `add_middleware` call is the **outermost** layer. It's an onion: the request goes in through each layer and the response comes back out through them.
- Use middleware for things that apply to **every** request: request IDs, timing, security headers, compression. For per-route needs such as auth, prefer **dependencies**, which are typed, testable and show up in docs.
- `@app.middleware("http")` is easy, but it wraps the response and doesn't suit streaming. High-performance middleware is written as **pure ASGI middleware** (a class with `__call__(scope, receive, send)`).

### CORS (the browser blocks it, not the server)
A page on `http://localhost:5173` calling `http://localhost:8000` is **cross-origin**. For non-simple requests (JSON bodies, custom headers, credentials), the browser first sends a **preflight** `OPTIONS` request, and the server has to answer with the right `Access-Control-Allow-*` headers.
```python
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.example.com"],
    allow_credentials=True,          # cookies / Authorization
    allow_methods=["*"], allow_headers=["*"],
    expose_headers=["X-Request-ID"]) # headers JS may read
```
- `allow_origins=["*"]` **with** credentials is invalid. Browsers reject it.
- CORS isn't security for your API. curl ignores it completely. It protects **users' browsers** from other sites using their cookies.
- Alternative: serve the API and the SPA from the same origin (a reverse proxy such as `/api` → FastAPI), and you don't need CORS at all.

### Lifespan (startup and shutdown)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()   # startup: DB pools, HTTP clients, ML models, cache warmup
    yield
    await app.state.pool.close()           # shutdown (graceful: SIGTERM during a deploy)

app = FastAPI(lifespan=lifespan)
```
This replaces the deprecated `@app.on_event("startup")`. It runs **once per worker process**, so with 4 workers you get 4 pools. In tests, `with TestClient(app):` triggers it.

### Background tasks
```python
@app.post("/signup", status_code=202)
def signup(data: Signup, background: BackgroundTasks):
    background.add_task(send_welcome_email, data.email)   # runs after the response is sent
    return {"status": "pending"}
```
They run **in the same process**. They're lost if the process dies, there are no retries, and they compete with requests for CPU. Use them for small, best-effort work (emails, cache warming). Use a **task queue** (Celery, RQ, Arq, Dramatiq, or cloud queues like SQS and Cloud Tasks) for anything that must be reliable, is slow, or needs retries or scheduling.

## 🏋️ Exercise
In `exercise/main.py`: add the request-ID and timing middleware, CORS for the React dev origin, lifespan, signup through `BackgroundTasks` (202), and GZip above 1000 bytes.
```bash
python check.py f13
```

## 💼 Interview angle
- *"Explain CORS and preflight."*: it's a browser same-origin protection. Non-simple requests trigger an OPTIONS preflight, and the server allow-lists origins, methods and headers. With credentials you can't use `*`.
- *"Middleware vs dependency?"*: middleware wraps everything (cross-cutting, untyped). Dependencies are per-route, typed, composable and overridable. Put auth in dependencies.
- *"Background tasks vs Celery?"*: in-process best-effort vs a durable queue with retries, scaling and scheduling. Background tasks disappear on deploys and crashes.
- *"Where do you initialise DB pools and clients?"*: in the lifespan, once per worker, closed on shutdown. Never per request, and never at import time.
- *"How do you trace a request across services?"*: generate or propagate `X-Request-ID` (or W3C `traceparent` with OpenTelemetry) and log it everywhere. R3 covers this.
