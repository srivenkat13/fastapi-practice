import time  # noqa: F401
import uuid  # noqa: F401
from contextlib import asynccontextmanager  # noqa: F401

from fastapi import BackgroundTasks, FastAPI, Request  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware  # noqa: F401
from fastapi.middleware.gzip import GZipMiddleware  # noqa: F401
from pydantic import BaseModel, EmailStr

FRONTEND_ORIGIN = "http://localhost:5173"  # your Vite/React dev server
STATE = {"started": False, "stopped": False}
OUTBOX: list[str] = []


def load_catalog() -> list[dict]:
    """Pretend this is expensive (loading an ML model, warming a cache, opening a pool)."""
    return [{"sku": "KB", "name": "Keyboard"}, {"sku": "MS", "name": "Mouse"}]


def send_welcome_email(email: str) -> None:
    time.sleep(0.01)  # pretend: SMTP call
    OUTBOX.append(email)


# TODO 3: lifespan: before yield set app.state.catalog = load_catalog() and STATE["started"] = True;
#         after yield set STATE["stopped"] = True. Pass it to FastAPI(lifespan=...).
app = FastAPI(title="F13 · Middleware")

# TODO 2: CORS for FRONTEND_ORIGIN only: allow_credentials=True, all methods/headers, expose "X-Request-ID"
# TODO 5: GZip responses larger than 1000 bytes


# TODO 1: an @app.middleware("http") that
#   - reuses the incoming X-Request-ID header or generates uuid.uuid4().hex
#   - stores it on request.state.request_id
#   - adds X-Request-ID and X-Process-Time-Ms (a number) headers to the response


@app.get("/catalog")
def catalog(request: Request):
    return request.app.state.catalog  # set by the lifespan


@app.get("/whoami")
def whoami(request: Request):
    return {"request_id": getattr(request.state, "request_id", None)}


class Signup(BaseModel):
    email: EmailStr


@app.post("/signup")  # TODO 4: return 202 {"status": "pending"} immediately; send the email in the background
def signup(data: Signup):
    send_welcome_email(data.email)
    return {"status": "sent"}


@app.get("/big")
def big():
    return [{"id": i, "description": "x" * 50} for i in range(200)]
