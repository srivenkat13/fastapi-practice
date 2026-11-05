import asyncio
import csv
import hashlib
import io
import json
from collections import defaultdict

from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

app = FastAPI(title="F14 · Files & streaming")

MAX_BYTES = 1024 * 1024  # 1 MB
CHUNK = 64 * 1024
SIGNATURES = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
AVATARS: dict[str, bytes] = {}  # stand-in for S3 / disk
BOOKS = [{"id": i, "title": f"Book {i}", "price_cents": 1000 + i} for i in range(1, 1001)]


# ---- 1) uploads ---------------------------------------------------------------------
@app.post("/avatars", status_code=201)
async def upload_avatar(file: UploadFile):
    if file.content_type not in SIGNATURES:
        raise HTTPException(415, "Only PNG or JPEG images are allowed")
    digest, size, chunks = hashlib.sha256(), 0, []
    while chunk := await file.read(CHUNK):  # stream in chunks; never trust Content-Length
        size += len(chunk)
        if size > MAX_BYTES:
            raise HTTPException(413, "File too large (max 1 MB)")
        digest.update(chunk)
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data.startswith(SIGNATURES[file.content_type]):  # the client-sent content type can lie
        raise HTTPException(415, "File content does not match its type")
    AVATARS[digest.hexdigest()] = data
    return {"filename": file.filename, "content_type": file.content_type, "size": size, "sha256": digest.hexdigest()}


# ---- 2) streaming a large CSV ---------------------------------------------------------
def csv_rows():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "title", "price_cents"])
    for book in BOOKS:  # in real life: iterate a DB cursor (yield_per) so memory stays flat
        writer.writerow([book["id"], book["title"], book["price_cents"]])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


@app.get("/export.csv")
def export_csv():
    return StreamingResponse(
        csv_rows(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="books.csv"'}
    )


# ---- 3) server-sent events ------------------------------------------------------------
async def progress_events(steps: int):
    for step in range(1, steps + 1):
        await asyncio.sleep(0.01)
        yield f"data: {json.dumps({'step': step, 'of': steps})}\n\n"  # SSE wire format
    yield "event: done\ndata: {}\n\n"


@app.get("/jobs/progress")
def job_progress(steps: int = 3):
    return StreamingResponse(progress_events(steps), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


# ---- 4) WebSocket chat rooms ----------------------------------------------------------
class RoomManager:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def join(self, room: str, ws: WebSocket):
        await ws.accept()
        self.rooms[room].add(ws)

    def leave(self, room: str, ws: WebSocket):
        self.rooms[room].discard(ws)

    async def broadcast(self, room: str, message: str):
        for ws in list(self.rooms[room]):
            await ws.send_text(message)


manager = RoomManager()  # per-process! multiple workers need Redis pub/sub to share rooms


@app.websocket("/ws/rooms/{room}")
async def chat(ws: WebSocket, room: str, name: str = "anon"):
    await manager.join(room, ws)
    await manager.broadcast(room, f"{name} joined")
    try:
        while True:
            text = await ws.receive_text()
            await manager.broadcast(room, f"{name}: {text}")
    except WebSocketDisconnect:
        manager.leave(room, ws)
        await manager.broadcast(room, f"{name} left")
