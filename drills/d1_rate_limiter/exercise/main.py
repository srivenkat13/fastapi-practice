import time
from collections import defaultdict, deque  # noqa: F401
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response  # noqa: F401


def get_clock() -> float:
    return time.monotonic()


def api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if not x_api_key:
        raise HTTPException(401, "Missing X-API-Key")
    return x_api_key


class RateLimiter:
    """⏱  25 minutes. Make an instance usable as a dependency: Depends(RateLimiter(limit=3, window=10)).

    - buckets per API key (from the `api_key` dependency); time from the `get_clock` dependency
    - SLIDING window: allow if fewer than `limit` requests in the last `window` seconds
    - over the limit: 429 with Retry-After (whole seconds until a slot frees up, at least 1)
    - allowed: set X-RateLimit-Limit and X-RateLimit-Remaining response headers
    - each instance keeps its own buckets
    """

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window


search_limiter = RateLimiter(limit=3, window=10)
export_limiter = RateLimiter(limit=1, window=60)
app = FastAPI(title="D1 · Rate limiter")


@app.get("/search")  # TODO: limit with search_limiter
def search(q: str = ""):
    return {"q": q, "results": []}


@app.post("/export")  # TODO: limit with export_limiter
def export():
    return {"status": "started"}


@app.get("/health")
def health():
    return {"status": "ok"}
