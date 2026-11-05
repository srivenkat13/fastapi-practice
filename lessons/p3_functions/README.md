# P3 · Functions, `*args`/`**kwargs`, closures, decorators

> FastAPI is built on decorators (`@app.get(...)`) and keyword arguments. Once you understand those two things, most of FastAPI stops looking like magic.

## 🧠 Concepts

### Parameters
```python
def create_user(name, role="member", *tags, active=True, **extra): ...
#               positional, default,  *args (tuple), keyword-only, **kwargs (dict)
create_user("ada", "admin", "vip", "beta", active=False, team="core")
#   name="ada", role="admin", tags=("vip","beta"), active=False, extra={"team": "core"}
```
- Parameters after `*` (or after `*args`) are **keyword-only**: `def f(a, *, b)` must be called as `f(1, b=2)`.
- Parameters before `/` are **positional-only**: `def f(a, /)`.
- Spread when calling: `f(*a_list, **a_dict)` is like `f(...arr)`, plus the same for named arguments.

### ⚠️ Mutable default arguments
```python
def add(item, bucket=[]):   # BUG: the same list is shared by every call!
def add(item, bucket=None):
    bucket = [] if bucket is None else bucket   # ✅
```
A default value is evaluated **once**, when the `def` statement runs. This is a classic interview question.

### Functions are objects, and closures work as in JS
```python
def make_counter():
    count = 0
    def inc():
        nonlocal count      # needed to *reassign* an enclosing variable
        count += 1
        return count
    return inc
```
`lambda x: x * 2` is a one-expression function. Use it for `key=` arguments, not for logic.

### Decorators = functions that wrap functions
```python
import functools

def log_calls(fn):
    @functools.wraps(fn)                 # keep fn.__name__, docstring and signature
    def wrapper(*args, **kwargs):
        print("calling", fn.__name__)
        return fn(*args, **kwargs)
    return wrapper

@log_calls          # same as: greet = log_calls(greet)
def greet(name): ...
```
A decorator **with arguments** is a factory that returns a decorator: `@retry(times=3)` → `retry(times=3)(fn)`.
`@app.get("/users")` is exactly this. It registers your function in a route table and returns it unchanged.

> `functools.wraps` also copies `__wrapped__`. FastAPI inspects signatures, so decorating an endpoint without `wraps` breaks parameter detection.

## 🏋️ Exercise
In `exercise.py`, implement `build_query`, fix `append_tag` (it has the mutable default bug), and write the `make_counter`, `retry`, `memoize` and `register` decorators.
```bash
python check.py p3
```

## 💼 Interview angle
- *"What's wrong with `def f(x=[])`?"*: the default is created once and shared between calls. Use `None` as a sentinel.
- *"Write a decorator that times or retries a function"*: show `functools.wraps`, `*args/**kwargs`, and the three-level version for decorators with arguments.
- *"What is `nonlocal` vs `global`?"*: they rebind a name in the enclosing function scope or the module scope.
- *"How does `@app.get` work?"*: it's a decorator factory. It registers the function and its signature, and FastAPI reads the type hints to build validation and docs.
- *"What does `functools.lru_cache` do?"*: it memoizes based on hashable arguments. FastAPI's docs use `@lru_cache` on `get_settings()`.
