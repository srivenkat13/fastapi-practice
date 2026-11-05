import asyncio
import time

import pytest

from support import target

m = target(__file__)
pytestmark = pytest.mark.anyio


async def slow_echo(x, delay=0.1):
    await asyncio.sleep(delay)
    return x


async def test_fetch_all_is_concurrent_and_ordered():
    start = time.perf_counter()
    assert await m.fetch_all([1, 2, 3, 4, 5], slow_echo) == [1, 2, 3, 4, 5]
    assert time.perf_counter() - start < 0.3, "fetches should run concurrently (~0.1s), not one by one (~0.5s)"


async def test_fetch_limited_respects_limit():
    in_flight = peak = 0

    async def tracked(x):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.05)
        in_flight -= 1
        return x * 10

    start = time.perf_counter()
    assert await m.fetch_limited(list(range(6)), tracked, 2) == [0, 10, 20, 30, 40, 50]
    assert peak == 2
    assert time.perf_counter() - start < 0.25


async def test_settled():
    async def boom():
        raise ValueError("nope")

    result = await m.settled([slow_echo("a", 0), boom(), slow_echo("c", 0)])
    assert result[0] == ("ok", "a") and result[2] == ("ok", "c")
    assert result[1][0] == "error" and isinstance(result[1][1], ValueError)


async def test_with_timeout():
    assert await m.with_timeout(slow_echo("fast", 0.01), 1) == "fast"
    start = time.perf_counter()
    assert await m.with_timeout(slow_echo("slow", 5), 0.05, default="fallback") == "fallback"
    assert time.perf_counter() - start < 0.5


async def test_run_blocking_keeps_loop_responsive():
    ticks = 0

    async def heartbeat():
        nonlocal ticks
        for _ in range(5):
            await asyncio.sleep(0.02)
            ticks += 1

    def blocking():
        time.sleep(0.15)
        return "done"

    result, _ = await asyncio.gather(m.run_blocking(blocking), heartbeat())
    assert result == "done"
    assert ticks == 5


async def test_ticker_is_async_generator():
    values = [v async for v in m.ticker(3, 0.01)]
    assert values == [0, 1, 2]
