"""A fake slow upstream microservice. Tests mount it in-process; `python -m uvicorn lessons.f12_async.upstream:app --port 9000` runs it for real."""
import asyncio

from fastapi import FastAPI

app = FastAPI(title="Fake upstream")
DELAY = 0.1


@app.get("/profile/{user_id}")
async def profile(user_id: int):
    await asyncio.sleep(DELAY)
    return {"id": user_id, "name": f"User {user_id}"}


@app.get("/orders/{user_id}")
async def orders(user_id: int):
    await asyncio.sleep(DELAY)
    return [{"id": 1, "total_cents": 4200}]


@app.get("/recommendations/{user_id}")
async def recommendations(user_id: int):
    await asyncio.sleep(DELAY)
    return ["Fluent Python", "Dune"]


@app.get("/quote")
async def quote():
    await asyncio.sleep(2)  # this upstream hangs
    return {"quote": "never arrives in time"}
