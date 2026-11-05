"""P8 exercise. `fetch` arguments are async functions like:  async def fetch(x): await asyncio.sleep(0.1); return x"""
import asyncio  # noqa: F401
from typing import Any, AsyncIterator, Awaitable, Callable


async def fetch_all(ids: list, fetch: Callable[[Any], Awaitable]) -> list:
    """Fetch every id CONCURRENTLY (Promise.all) and return results in the same order as ids."""
    results = []
    for i in ids:  # 🐛 sequential: 5 x 100ms = 500ms
        results.append(await fetch(i))
    return results


async def fetch_limited(ids: list, fetch: Callable[[Any], Awaitable], limit: int) -> list:
    """Like fetch_all, but never more than `limit` fetches in flight at once (asyncio.Semaphore)."""
    raise NotImplementedError


async def settled(coros: list[Awaitable]) -> list[tuple[str, Any]]:
    """Promise.allSettled: return [("ok", value) | ("error", exception), ...] in order."""
    raise NotImplementedError


async def with_timeout(coro: Awaitable, seconds: float, default: Any = None) -> Any:
    """Await coro, but return `default` if it takes longer than `seconds`."""
    raise NotImplementedError


async def run_blocking(fn: Callable, *args) -> Any:
    """Run a BLOCKING function (e.g. one that calls time.sleep) without freezing the event loop."""
    raise NotImplementedError


async def ticker(count: int, delay: float) -> AsyncIterator[int]:
    """An async generator yielding 0..count-1, sleeping `delay` seconds between values."""
    raise NotImplementedError
    yield
