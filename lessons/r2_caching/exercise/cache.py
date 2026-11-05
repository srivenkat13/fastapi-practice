"""A tiny cache with the same shape as a Redis client. Implement it, then use it in main.py."""
import asyncio  # noqa: F401
import time
from collections import defaultdict  # noqa: F401
from typing import Any, Awaitable, Callable

MISSING = object()  # sentinel returned by get() for absent/expired keys (so `None` can be cached)


class InMemoryCache:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        """`clock` returns "now" in seconds; tests pass a fake one. Also create self.locks: one asyncio.Lock per key."""
        raise NotImplementedError

    def get(self, key: str) -> Any:
        """Value, or MISSING if absent or expired (expired entries should be removed)."""
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: float) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError


async def get_or_load(cache: InMemoryCache, key: str, loader: Callable[[], Awaitable[Any]], ttl: float) -> tuple[Any, bool]:
    """Cache-aside + single-flight. Return (value, hit).
    On a miss, hold cache.locks[key] while loading so 5 concurrent misses cause ONE loader() call
    (re-check the cache after acquiring the lock)."""
    raise NotImplementedError
