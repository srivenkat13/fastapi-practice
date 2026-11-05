# P8 · `async`/`await` and the event loop

> You already know JS promises. Python's `asyncio` is the same idea (a single-threaded event loop) with one key difference: **a blocking call freezes everything**, and Python has many blocking libraries. Knowing when to use `async def` vs `def` is the most important FastAPI performance topic.

## 🧠 Concepts

### JS → Python
| JS | Python (`asyncio`) |
|---|---|
| `async function f()` | `async def f():` |
| `await p` | `await coro` |
| calling `f()` starts it immediately | calling `f()` creates a **coroutine object** that does nothing until awaited or scheduled |
| `Promise.all([...])` | `await asyncio.gather(a(), b())` |
| `Promise.allSettled` | `asyncio.gather(..., return_exceptions=True)` |
| `Promise.race` + timeout | `async with asyncio.timeout(2):` / `asyncio.wait_for(coro, 2)` |
| `setTimeout(r, 100)` | `await asyncio.sleep(0.1)` |
| fire-and-forget promise | `asyncio.create_task(coro)` (keep a reference!) |
| `for await (x of gen)` | `async for x in agen:` |
| limit concurrency (p-limit) | `asyncio.Semaphore(n)` |
| top-level script | `asyncio.run(main())` |

### Blocking the loop
```python
async def handler():
    time.sleep(2)              # ❌ blocks the event loop; every other request waits
    requests.get(url)          # ❌ a sync HTTP client does the same
    await asyncio.sleep(2)     # ✅
    await httpx.AsyncClient().get(url)          # ✅ an async client
    await asyncio.to_thread(blocking_fn, arg)   # ✅ run sync code in a worker thread
```
- **CPU-bound** work (image processing, heavy loops) blocks even inside threads, because of the GIL. Use a process pool or a task queue.
- Python 3.13+ has an optional free-threaded build (no GIL), but it isn't the default yet.

### Threads, processes, async
| Workload | Tool |
|---|---|
| lots of waiting on I/O (HTTP, DB) | `asyncio` |
| blocking I/O libraries you can't change | threads (`asyncio.to_thread`, `ThreadPoolExecutor`) |
| CPU-heavy | processes (`ProcessPoolExecutor`), or Celery/RQ workers |

### Structured concurrency (3.11+)
```python
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(fetch("a"))
    t2 = tg.create_task(fetch("b"))
# here both are done; if one fails, the others are cancelled and an ExceptionGroup is raised
```

## 🏋️ Exercise
Implement the coroutines in `exercise.py`. The tests measure wall-clock time, so sequential awaits will fail.
```bash
python check.py p8
```

## 💼 Interview angle
- *"What happens if you call `time.sleep` in an `async def` FastAPI endpoint?"*: the whole worker's event loop stalls, and every concurrent request waits. Use `await asyncio.sleep`, an async library, `def` (FastAPI then runs it in a threadpool), or `to_thread`.
- *"What is the GIL and does it matter for web APIs?"*: only one thread runs Python bytecode at a time. I/O releases it, so I/O-bound APIs scale fine with async or threads. CPU-bound work needs processes.
- *"gather vs TaskGroup?"*: a TaskGroup cancels its siblings on failure and raises an ExceptionGroup, which is safer. `gather` with `return_exceptions=True` is "allSettled".
- *"How do you limit concurrency to an upstream API?"*: an `asyncio.Semaphore`, plus timeouts and retries with backoff.
- *"Coroutine vs Task?"*: a coroutine is a paused function. A Task wraps it and schedules it on the loop so it runs concurrently.
