import asyncio
import time
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Note, create_tables, get_async_session

UPSTREAM_URL = "http://127.0.0.1:9000"
QUOTE_TIMEOUT = 0.3


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    async with httpx.AsyncClient(base_url=UPSTREAM_URL) as client:
        app.state.http = client
        yield


app = FastAPI(title="F12 · Async", lifespan=lifespan)


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


Http = Annotated[httpx.AsyncClient, Depends(get_http)]


@app.get("/dashboard/{user_id}")
async def dashboard(user_id: int, http: Http):
    profile, orders, recs = await asyncio.gather(
        http.get(f"/profile/{user_id}"),
        http.get(f"/orders/{user_id}"),
        http.get(f"/recommendations/{user_id}"),
    )
    return {"profile": profile.json(), "orders": orders.json(), "recommendations": recs.json()}


def generate_report() -> dict:
    time.sleep(0.2)
    return {"report": "ready"}


# Option A: a plain `def` endpoint, which FastAPI runs in a threadpool so the loop stays free.
@app.get("/report")
def report():
    return generate_report()


# Option B (when the endpoint must stay async for other awaits):
#     return await asyncio.to_thread(generate_report)


@app.get("/quote")
async def quote(http: Http):
    try:
        async with asyncio.timeout(QUOTE_TIMEOUT):
            data = (await http.get("/quote")).json()
    except (TimeoutError, httpx.HTTPError):
        return {"quote": None, "degraded": True}  # graceful degradation instead of a hung request
    return {"quote": data["quote"], "degraded": False}


class NoteIn(BaseModel):
    text: str


Session = Annotated[AsyncSession, Depends(get_async_session)]


@app.post("/notes", status_code=201)
async def create_note(data: NoteIn, session: Session):
    note = Note(text=data.text)
    session.add(note)  # add() is sync: it only stages the object
    await session.commit()  # I/O → await
    return {"id": note.id, "text": note.text}


@app.get("/notes")
async def list_notes(session: Session):
    notes = await session.scalars(select(Note).order_by(Note.id))
    return [{"id": n.id, "text": n.text} for n in notes]
