import asyncio  # noqa: F401
import csv  # noqa: F401
import hashlib  # noqa: F401
import io  # noqa: F401
import json  # noqa: F401
from collections import defaultdict  # noqa: F401

from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect  # noqa: F401
from fastapi.responses import StreamingResponse  # noqa: F401

app = FastAPI(title="F14 · Files & streaming")

MAX_BYTES = 1024 * 1024  # 1 MB
CHUNK = 64 * 1024
SIGNATURES = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
AVATARS: dict[str, bytes] = {}
BOOKS = [{"id": i, "title": f"Book {i}", "price_cents": 1000 + i} for i in range(1, 1001)]


@app.post("/avatars", status_code=201)
async def upload_avatar(file: UploadFile):
    """TODO 1:
    - content_type must be a key of SIGNATURES, else 415
    - read in CHUNK-sized pieces (await file.read(CHUNK)); if total > MAX_BYTES -> 413 (stop reading!)
    - the bytes must start with SIGNATURES[content_type] (magic bytes), else 415
    - store in AVATARS[sha256] and return {"filename", "content_type", "size", "sha256"}
    """
    data = await file.read()  # 🐛 reads everything into memory, no checks at all
    return {"filename": file.filename, "size": len(data)}


@app.get("/export.csv")
def export_csv():
    """TODO 2: StreamingResponse over a generator that yields the CSV line by line
    (header "id,title,price_cents" then one row per book), media_type "text/csv",
    header Content-Disposition: attachment; filename="books.csv"
    """
    lines = ["id,title,price_cents"] + [f"{b['id']},{b['title']},{b['price_cents']}" for b in BOOKS]
    return "\n".join(lines)  # 🐛 one huge JSON string, built in memory


@app.get("/jobs/progress")
def job_progress(steps: int = 3):
    """TODO 3: Server-Sent Events (media_type "text/event-stream"). For each step yield
    'data: {"step": n, "of": steps}\n\n' (JSON), then finally 'event: done\ndata: {}\n\n'."""
    raise HTTPException(501, "Not implemented")


@app.websocket("/ws/rooms/{room}")
async def chat(ws: WebSocket, room: str, name: str = "anon"):
    """TODO 4: chat rooms.
    - on connect: accept, add to the room, broadcast "<name> joined" to everyone in the room (including them)
    - each text message: broadcast "<name>: <text>" to the room
    - on WebSocketDisconnect: remove them, broadcast "<name> left"
    Rooms are isolated: messages in "python" never reach "rust".
    """
    await ws.accept()
    while True:
        text = await ws.receive_text()
        await ws.send_text(text)  # 🐛 just echoes to the sender
