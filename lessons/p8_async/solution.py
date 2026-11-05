"""P8 reference solution."""
import asyncio
from typing import Any, AsyncIterator, Awaitable, Callable


async def fetch_all(ids, fetch):
    return await asyncio.gather(*(fetch(i) for i in ids))  # gather preserves order


async def fetch_limited(ids, fetch, limit):
    semaphore = asyncio.Semaphore(limit)

    async def one(i):
        async with semaphore:
            return await fetch(i)

    return await asyncio.gather(*(one(i) for i in ids))


async def settled(coros):
    results = await asyncio.gather(*coros, return_exceptions=True)
    return [("error", r) if isinstance(r, BaseException) else ("ok", r) for r in results]


async def with_timeout(coro: Awaitable, seconds: float, default: Any = None) -> Any:
    try:
        async with asyncio.timeout(seconds):  # 3.11+; asyncio.wait_for works too
            return await coro
    except TimeoutError:
        return default


async def run_blocking(fn: Callable, *args) -> Any:
    return await asyncio.to_thread(fn, *args)


async def ticker(count: int, delay: float) -> AsyncIterator[int]:
    for i in range(count):
        if i:
            await asyncio.sleep(delay)
        yield i
