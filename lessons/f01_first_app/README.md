# F01 · Your first FastAPI app, `/docs`, and the request lifecycle

> FastAPI = **Starlette** (the async web toolkit: routing, requests, responses, middleware, WebSockets) + **Pydantic** (validation and serialization, driven by type hints) + automatic **OpenAPI** docs. You write normal functions with type hints, and FastAPI handles the HTTP work.

## 🧠 Concepts

### The minimal app
```python
from fastapi import FastAPI

app = FastAPI(title="Bookshelf API", version="0.1.0")

@app.get("/health", tags=["meta"], summary="Liveness probe")
def health():
    return {"status": "ok"}       # dicts, lists and Pydantic models become JSON
```
Run it with `python run.py f01`. That calls uvicorn, roughly `uvicorn lessons.f01_first_app.exercise.main:app --reload`. Then open:
- **http://127.0.0.1:8000/docs**: interactive Swagger UI ("Try it out")
- **/redoc**: alternative docs
- **/openapi.json**: the machine-readable spec (used for generating TS clients: `openapi-typescript`, `orval`)

> The official CLI does the same: `fastapi dev path/to/main.py` (dev with reload) and `fastapi run` (production).

### What happens on a request
```
client → uvicorn (ASGI server: parses HTTP, manages connections)
       → middleware stack (CORS, GZip, your own...)          [F13]
       → router: match method + path → your endpoint
       → resolve dependencies (Depends)                      [F06]
       → parse + validate path/query/headers/body (Pydantic) [F02-F03] → 422 on failure
       → call your function (def → threadpool, async def → event loop)  [F12]
       → validate/serialize return value via response_model  [F04]
       → JSON response back through the middleware
```

### ASGI vs WSGI
- **WSGI** (Flask, Django classic): one request per worker thread, synchronous. Server: gunicorn.
- **ASGI** (FastAPI, Starlette, Django async): async-native, so one process handles thousands of concurrent I/O-bound requests, and it supports WebSockets and streaming. Servers: uvicorn, hypercorn, granian.

### Express mental model
| Express | FastAPI |
|---|---|
| `const app = express()` | `app = FastAPI()` |
| `app.get('/x', (req, res) => res.json(...))` | `@app.get("/x")` + `return {...}` |
| `req.params.id` / `req.query.q` | function parameters with type hints |
| `express.Router()` | `APIRouter()` [F07] |
| middleware `(req,res,next)` | `@app.middleware("http")` / Starlette middleware [F13] |
| manual validation (zod, joi) | automatic from type hints and Pydantic |
| swagger-jsdoc by hand | automatic `/docs` |

## 🏋️ Exercise
Edit `exercise/main.py`:
1. Give the app the title **"Bookshelf API"** and version **"0.1.0"**.
2. Add `GET /health` → `{"status": "ok"}` with tag `meta`.
3. Add `GET /books` → the `BOOKS` list, with tag `books` and summary "List all books".
4. Run it (`python run.py f01`) and use **Try it out** in `/docs`.

```bash
python check.py f01
```

## 💼 Interview angle
- *"Why is FastAPI fast?"*: it runs on ASGI and Starlette with async I/O, and Pydantic v2's core is written in Rust. Developer speed counts too: validation and docs come from types.
- *"ASGI vs WSGI?"*: async-native vs sync-per-request. ASGI supports WebSockets, streaming and long-lived connections.
- *"What is uvicorn and why does FastAPI need it?"*: FastAPI is only an ASGI application, so you need an ASGI server to speak HTTP. In production you run several worker processes (`fastapi run --workers 4` / `uvicorn --workers`, or gunicorn with uvicorn workers).
- *"How do frontend teams consume a FastAPI backend?"*: they generate a typed client from `/openapi.json`, so the backend's types become the frontend's TS types.
