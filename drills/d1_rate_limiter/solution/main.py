import math
import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response


def get_clock() -> float:
    return time.monotonic()


def api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if not x_api_key:
        raise HTTPException(401, "Missing X-API-Key")
    return x_api_key


class RateLimiter:
    """Sliding-window log: remember each request's timestamp per key; allow if < limit in the last `window` seconds.
    A callable instance is a valid dependency, so each instance has its own buckets and settings."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def __call__(self, response: Response, key: Annotated[str, Depends(api_key)], now: Annotated[float, Depends(get_clock)]):
        hits = self.hits[key]
        while hits and hits[0] <= now - self.window:  # drop timestamps outside the window (O(1) amortised)
            hits.popleft()
        if len(hits) >= self.limit:
            retry_after = max(1, math.ceil(hits[0] + self.window - now))
            raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": str(retry_after), "X-RateLimit-Remaining": "0"})
        hits.append(now)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(self.limit - len(hits))


search_limiter = RateLimiter(limit=3, window=10)
export_limiter = RateLimiter(limit=1, window=60)
app = FastAPI(title="D1 · Rate limiter")


@app.get("/search", dependencies=[Depends(search_limiter)])
def search(q: str = ""):
    return {"q": q, "results": []}


@app.post("/export", dependencies=[Depends(export_limiter)])
def export():
    return {"status": "started"}


@app.get("/health")  # not rate limited
def health():
    return {"status": "ok"}
