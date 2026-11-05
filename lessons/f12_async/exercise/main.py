import asyncio  # noqa: F401
import time
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from sqlalchemy import select  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Note, create_tables, get_async_session  # noqa: F401

UPSTREAM_URL = "http://127.0.0.1:9000"
QUOTE_TIMEOUT = 0.3


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    # ONE shared client for the app's lifetime: connection pooling, keep-alive.
    async with httpx.AsyncClient(base_url=UPSTREAM_URL) as client:
        app.state.http = client
        yield


app = FastAPI(title="F12 · Async", lifespan=lifespan)


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


Http = Annotated[httpx.AsyncClient, Depends(get_http)]


# 1) 🐛 Three independent upstream calls made one after another (~300ms). Run them concurrently.
@app.get("/dashboard/{user_id}")
async def dashboard(user_id: int, http: Http):
    profile = (await http.get(f"/profile/{user_id}")).json()
    orders = (await http.get(f"/orders/{user_id}")).json()
    recs = (await http.get(f"/recommendations/{user_id}")).json()
    return {"profile": profile, "orders": orders, "recommendations": recs}


# 2) 🐛 A blocking library call inside `async def` freezes the event loop for EVERY request.
def generate_report() -> dict:
    time.sleep(0.2)  # pretend: a sync PDF library / sync DB driver / requests.get(...)
    return {"report": "ready"}


@app.get("/report")
async def report():
    return generate_report()


# 3) TODO: call GET /quote upstream, but give up after QUOTE_TIMEOUT seconds and return
#    {"quote": None, "degraded": True}. On success return {"quote": <upstream quote>, "degraded": False}.
@app.get("/quote")
async def quote(http: Http):
    data = (await http.get("/quote")).json()
    return {"quote": data["quote"], "degraded": False}


# 4) TODO: async DB endpoints
class NoteIn(BaseModel):
    text: str


Session = Annotated[AsyncSession, Depends(get_async_session)]


@app.post("/notes", status_code=201)
async def create_note(data: NoteIn, session: Session):
    """TODO: add a Note, `await session.commit()`, return {"id": ..., "text": ...}"""
    raise NotImplementedError


@app.get("/notes")
async def list_notes(session: Session):
    """TODO: `result = await session.scalars(select(Note).order_by(Note.id))` -> [{"id", "text"}, ...]"""
    raise NotImplementedError
