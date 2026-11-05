import time
import uuid
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, EmailStr

FRONTEND_ORIGIN = "http://localhost:5173"
STATE = {"started": False, "stopped": False}
OUTBOX: list[str] = []


def load_catalog() -> list[dict]:
    return [{"sku": "KB", "name": "Keyboard"}, {"sku": "MS", "name": "Mouse"}]


def send_welcome_email(email: str) -> None:
    time.sleep(0.01)
    OUTBOX.append(email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: runs once per worker process, before the first request
    app.state.catalog = load_catalog()
    STATE["started"] = True
    yield
    # shutdown: close pools, flush buffers
    STATE["stopped"] = True


app = FastAPI(title="F13 · Middleware", lifespan=lifespan)

# Middleware order: the LAST added is the OUTERMOST. CORS should be outermost so even errors carry CORS headers.
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],  # never "*" together with credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # let browser JS read this response header
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.2f}"
    return response


@app.get("/catalog")
def catalog(request: Request):
    return request.app.state.catalog


@app.get("/whoami")
def whoami(request: Request):
    return {"request_id": request.state.request_id}


class Signup(BaseModel):
    email: EmailStr


@app.post("/signup", status_code=202)
def signup(data: Signup, background: BackgroundTasks):
    background.add_task(send_welcome_email, data.email)  # runs after the response is sent
    return {"status": "pending"}


@app.get("/big")
def big():
    return [{"id": i, "description": "x" * 50} for i in range(200)]
