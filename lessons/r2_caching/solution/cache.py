"""A tiny cache with the same shape as a Redis client (get / set with TTL / delete).

Swapping in Redis later:
    import redis.asyncio as redis
    r = redis.from_url("redis://localhost:6379")
    await r.set(key, json.dumps(value), ex=ttl); json.loads(await r.get(key) or "null")
"""
import asyncio
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

MISSING = object()  # sentinel: lets us cache `None` (negative caching) and still tell "absent" apart


class InMemoryCache:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._data: dict[str, tuple[float, Any]] = {}
        self.locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def get(self, key: str) -> Any:
        entry = self._data.get(key)
        if entry is None:
            return MISSING
        expires_at, value = entry
        if self._clock() >= expires_at:
            del self._data[key]  # lazy expiry, like Redis's passive expiration
            return MISSING
        return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._data[key] = (self._clock() + ttl, value)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


async def get_or_load(cache: InMemoryCache, key: str, loader: Callable[[], Awaitable[Any]], ttl: float) -> tuple[Any, bool]:
    """Cache-aside with single-flight: concurrent misses for one key trigger ONE load. Returns (value, hit)."""
    value = cache.get(key)
    if value is not MISSING:
        return value, True
    async with cache.locks[key]:
        value = cache.get(key)  # double-checked: another request may have filled it while we waited
        if value is not MISSING:
            return value, True
        value = await loader()
        cache.set(key, value, ttl)
        return value, False
