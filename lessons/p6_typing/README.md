# P6 · Type hints in depth (FastAPI runs on these)

> In TypeScript, types disappear at runtime. In Python, **type hints are runtime objects** that any library can inspect. FastAPI and Pydantic read your hints to validate requests, convert types, and generate OpenAPI docs. In this lesson you'll build a small version of that mechanism yourself.

## 🧠 Concepts

### TS → Python typing
| TypeScript | Python |
|---|---|
| `string`, `number`, `boolean` | `str`, `int` / `float`, `bool` |
| `string[]` | `list[str]` |
| `Record<string, number>` | `dict[str, int]` |
| `[string, number]` | `tuple[str, int]` |
| `string \| null` | `str \| None` (older code: `Optional[str]`) |
| `"a" \| "b"` | `Literal["a", "b"]` |
| `any` / `unknown` | `Any` / `object` |
| `type User = {id: number; email?: string}` | `class User(TypedDict): id: int; email: NotRequired[str]` |
| `interface Closeable { close(): void }` (structural) | `class Closeable(Protocol): def close(self) -> None: ...` |
| `function first<T>(xs: T[]): T` | `T = TypeVar("T")`; `def first(xs: list[T]) -> T` (3.12+: `def first[T](xs: list[T]) -> T`) |
| `(x: number) => string` | `Callable[[int], str]` |

- **Python doesn't enforce hints.** `def f(x: int)` happily accepts `"hi"`. Enforcement comes from a static checker (mypy, pyright/Pylance in VS Code) or from runtime libraries like **Pydantic**.
- `Protocol` gives structural typing, which is TS's default. Normal classes are nominal.

### `Annotated`: types plus metadata
```python
from typing import Annotated
PageSize = Annotated[int, Range(1, 100)]     # the type is int, and Range is extra information
def list_users(limit: PageSize = 20): ...
```
Type checkers see plain `int`. Libraries can read the metadata. FastAPI uses exactly this:
`limit: Annotated[int, Query(ge=1, le=100)] = 20`.

### Reading hints at runtime
```python
import inspect, typing
sig = inspect.signature(fn)                        # parameter names, defaults, kinds
hints = typing.get_type_hints(fn, include_extras=True)   # {"limit": Annotated[int, Range(1, 100)], ...}
typing.get_origin(Annotated[int, X])   # -> Annotated
typing.get_args(Annotated[int, X])     # -> (int, X)
typing.get_origin(int | None)          # -> types.UnionType  (typing.Union for Optional[int])
typing.get_args(int | None)            # -> (int, NoneType)
```

## 🏋️ Exercise
In `exercise.py`:
1. `first()`, a generic function using a `TypeVar`.
2. `UserDict`, a `TypedDict` with an optional `email`.
3. `Closeable`, a `@runtime_checkable` Protocol, plus `close_all()`.
4. **`call_with_query(fn, query)`**, a toy FastAPI. Read `fn`'s signature and hints, convert the query-string values (all `str`) to `int` / `float` / `bool` / `str`, apply defaults, treat `X | None` as optional, enforce `Annotated[..., Range(lo, hi)]`, and collect **all** errors into one `ValidationFailed`. (FastAPI returns those errors as a 422 response.)

```bash
python check.py p6
```

## 💼 Interview angle
- *"Does Python enforce type hints?"*: no. They're metadata for checkers and libraries. Pydantic and FastAPI enforce them at runtime, at your system's edges.
- *"How does FastAPI know `limit` is a query param and `user` is a body?"*: it inspects the signature. Simple types that aren't in the path become query params, Pydantic models become the body, and `Annotated[..., Query/Path/Body/Header/Depends]` makes it explicit.
- *"Protocol vs ABC?"*: a Protocol is structural, so there's no inheritance needed (duck typing with checks). An ABC is nominal and can enforce abstract methods at instantiation.
- *"What's `Annotated` for?"*: it attaches metadata without changing the type. It's the modern FastAPI style (and reusable: `CurrentUser = Annotated[User, Depends(get_user)]`).
- *"mypy vs pyright?"*: both are static checkers. Pyright (Pylance) is faster and powers VS Code. Run one in CI.
