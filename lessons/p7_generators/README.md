# P7 · Iterators, generators, `yield`

> FastAPI's **dependencies with `yield`** (DB sessions), **`StreamingResponse`** and **lifespan** all depend on generators. Python generators work much like JS generators (`function*`), but they're used far more often.

## 🧠 Concepts

### The iterator protocol
`for x in thing` calls `iter(thing)` and then `next()` repeatedly until `StopIteration` is raised. A class can take part by defining `__iter__` (which returns self) and `__next__`.

### Generators make this easy
```python
def countdown(n):
    while n > 0:
        yield n        # pause here and hand back a value
        n -= 1

gen = countdown(3)     # nothing runs yet (lazy!)
next(gen)  # 3
list(gen)  # [2, 1]    (a generator is single-use)
```
- **Generator expressions**: `(x * 2 for x in nums)` is a lazy version of a list comprehension. Use it with `sum(...)`, `any(...)` and so on.
- Laziness gives **constant memory** for huge files or paginated APIs, plus early exit.
- `yield from other_gen` delegates to another generator.
- `itertools`: `islice` (take n), `chain`, `groupby`, `batched` (3.12+), `count`.

### `yield` for setup and teardown
```python
def get_db():
    db = Session()
    try:
        yield db       # the request runs while we're paused here
    finally:
        db.close()     # runs after the response, even on errors
```
That's a FastAPI dependency (lesson F06). `@contextmanager` (P4) and FastAPI's `lifespan` use the same idea.

### JS comparison
| JS | Python |
|---|---|
| `function* g() { yield 1 }` | `def g(): yield 1` |
| `for (const x of g())` | `for x in g():` |
| `async function*` + `for await` | `async def` + `yield` → `async for` (P8) |

## 🏋️ Exercise
Implement the generators in `exercise.py`, including a lazy paginator. The test counts API calls to prove it's lazy.
```bash
python check.py p7
```

## 💼 Interview angle
- *"Generator vs list?"*: a generator is lazy, uses O(1) memory and can only be consumed once. A list is materialised and can be reused and indexed.
- *"How would you process a 10 GB log file?"*: iterate the file object line by line (files are iterators) through a generator pipeline. Never `read()` it all.
- *"What happens to the code after `yield` in a FastAPI dependency?"*: it runs after the response is sent (teardown). Exceptions from the endpoint are re-raised at the `yield`, so `try/finally` (or `except`, then re-raise) handles cleanup.
- *"What does `yield from` do?"*: it delegates to a sub-iterator (and forwards `send`/`throw`).
