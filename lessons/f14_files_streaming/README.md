# F14 · Uploads, streaming responses, SSE, WebSockets

> Not everything is a small JSON object. This lesson covers safe uploads, exports too big for memory, live progress, and two-way real-time communication.

## 🧠 Concepts

### Uploads
```python
@app.post("/avatars")
async def upload(file: UploadFile):          # multipart/form-data (needs python-multipart)
    file.filename, file.content_type
    chunk = await file.read(64 * 1024)       # a SpooledTemporaryFile: in memory when small, on disk when big
```
Security checklist:
- **Size limit**, enforced while reading (and at the proxy: nginx `client_max_body_size`).
- **Type allow-list** that checks **magic bytes**, because `content_type` and the extension are client-controlled.
- Never use `file.filename` as a filesystem path (path traversal: `../../etc/passwd`). Generate names yourself (uuid or content hash).
- Store in object storage (S3/GCS), not on the app server's disk. For large files, use **presigned upload URLs**: the browser uploads straight to S3 and your API only signs the request.

### StreamingResponse
```python
def rows():
    yield "id,title\n"
    for book in db_cursor: yield f"{book.id},{book.title}\n"

return StreamingResponse(rows(), media_type="text/csv",
                         headers={"Content-Disposition": 'attachment; filename="books.csv"'})
```
Memory stays flat no matter how big the export is (P7 generators at work). Also used for proxying, large files (or `FileResponse`), and **LLM token streaming**.

### Server-Sent Events (one-way server → browser)
```
data: {"step": 1}\n\n          ← each event ends with a blank line
event: done\ndata: {}\n\n      ← named event
```
Browser: `new EventSource("/jobs/progress")`. It runs over plain HTTP and auto-reconnects. Use it for notifications, progress bars and ChatGPT-style streaming.

### WebSockets (two-way)
```python
@app.websocket("/ws/rooms/{room}")
async def chat(ws: WebSocket, room: str):
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            await ws.send_text(msg)
    except WebSocketDisconnect: ...
```
- **Scaling**: connections live in one process. With several workers or pods, broadcast through **Redis pub/sub** (or NATS/Kafka), and use sticky sessions at the load balancer when needed.
- Auth: browsers can't set headers on WebSocket connections, so send a token as a query param or a first message, or rely on the cookie. Validate before `accept()`.

| Need | Use |
|---|---|
| request/response | REST |
| server pushes updates | SSE (simpler, HTTP-native) |
| two-way, low latency (chat, multiplayer, collaboration) | WebSocket |
| very occasional updates | polling |

## 🏋️ Exercise
In `exercise/main.py`, implement the safe avatar upload (415/413, magic bytes, sha256), the streamed CSV export, the SSE progress endpoint, and WebSocket chat rooms.
```bash
python check.py f14
```
Try the chat yourself: run `python run.py f14 --solution`, then in the browser console:
`ws = new WebSocket("ws://127.0.0.1:8000/ws/rooms/python?name=me"); ws.onmessage = e => console.log(e.data); ws.send("hi")`

## 💼 Interview angle
- *"How do you handle large file uploads?"*: presigned URLs straight to S3, size limits at the proxy and the app, type checks, and async virus or format scanning afterwards.
- *"How do you export 10M rows?"*: stream from a server-side cursor with a generator, or create an async job that writes to S3 and email a link.
- *"SSE vs WebSockets?"*: SSE is one-way, works over HTTP/2 and through proxies, and auto-reconnects. WebSockets are full-duplex but need more infrastructure (sticky sessions, pub/sub).
- *"How do you scale WebSockets across instances?"*: shared pub/sub (Redis), connection registries, and sticky load balancing, plus heartbeats and timeouts for dead connections.
