# Python for JS/TS developers: a one-page cheat sheet

Keep this open while you do the P lessons.

## Syntax
| JS / TS | Python |
|---|---|
| `const x = 1; let y = 2` | `x = 1` (no declarations; `UPPER_CASE` marks a "constant") |
| `{ ... }` blocks | indentation (4 spaces) + `:` |
| `null`, `undefined` | `None` |
| `true && false \|\| !x` | `True and False or not x` |
| `===` | `==`   (identity: `is`) |
| `a ?? b` | `a if a is not None else b` |
| `cond ? a : b` | `a if cond else b` |
| `` `${a} + ${b}` `` | `f"{a} + {b}"` |
| `// comment`, `/* */` | `# comment`, `"""docstring"""` |
| `typeof x === 'string'` | `isinstance(x, str)` |
| `throw new Error('x')` | `raise ValueError("x")` |
| `try {} catch (e) {} finally {}` | `try: ... except ValueError as e: ... finally: ...` |
| `x?.y?.z` | no built-in; `getattr(x, "y", None)`, `d.get("y", {}).get("z")` |
| `...spread` | `*args` / `**kwargs`, `[*a, *b]`, `{**a, **b}` |
| `const {a, b} = obj` | `a, b = obj["a"], obj["b"]` (tuples destructure: `a, b = pair`) |
| `const [first, ...rest] = arr` | `first, *rest = arr` |
| `import x from './x'` | `from .x import thing` / `import x` |
| `export default` | everything at module level is importable; `__all__` lists the public API |

## Collections
| JS | Python |
|---|---|
| `arr.length` | `len(arr)` |
| `arr.push(x)` / `pop()` | `lst.append(x)` / `lst.pop()` |
| `arr.map(f)` | `[f(x) for x in lst]` |
| `arr.filter(p)` | `[x for x in lst if p(x)]` |
| `arr.reduce(...)` | `sum()`, `max()`, `functools.reduce` (rarely needed) |
| `arr.some/every` | `any(...)` / `all(...)` |
| `arr.find(p)` | `next((x for x in lst if p(x)), None)` |
| `arr.slice(1, 3)` | `lst[1:3]` (also `lst[-1]`, `lst[::-1]`) |
| `arr.includes(x)` | `x in lst` |
| `arr.sort((a,b) => a.n - b.n)` | `lst.sort(key=lambda a: a.n)` / `sorted(...)` |
| `Object.keys/values/entries(o)` | `d.keys()`, `d.values()`, `d.items()` |
| `o.key ?? def` | `d.get("key", default)` |
| `new Set(arr)` | `set(lst)` |
| `new Map()` | `dict()` (keys can be any hashable) |
| `arr.forEach((x, i) => ...)` | `for i, x in enumerate(lst):` |
| `JSON.stringify / parse` | `json.dumps / json.loads` |

## Functions & classes
| JS | Python |
|---|---|
| `(a, b = 2) => a + b` | `def f(a, b=2): return a + b` / `lambda a, b=2: a + b` |
| options object `f({ a, b })` | keyword args `f(a=1, b=2)` |
| `class A extends B { constructor() { super() } }` | `class A(B): def __init__(self): super().__init__()` |
| `this.x` | `self.x` (explicit first parameter) |
| `get x() {}` | `@property def x(self): ...` |
| `static f()` | `@staticmethod` / `@classmethod` |
| `#private` | `_convention` (`__mangled` exists but is rarely used) |
| TS `interface` | `Protocol` (structural) / `TypedDict` (dict shapes) / Pydantic model |

## Async
| JS | Python |
|---|---|
| `async/await` | `async/await` (same idea) |
| `Promise.all` | `asyncio.gather(...)` |
| `Promise.allSettled` | `gather(..., return_exceptions=True)` |
| `setTimeout` | `await asyncio.sleep(s)` |
| top-level await | `asyncio.run(main())` |
| everything is non-blocking by default | ⚠️ many libraries are **blocking**: `requests`, `time.sleep`, sync DB drivers |

## Tooling
| Node | Python |
|---|---|
| nvm | pyenv / `uv python` |
| npm / pnpm | pip / **uv** / poetry |
| package.json | pyproject.toml |
| node_modules (auto) | `.venv` (create + activate) |
| npx | `python -m`, pipx, uvx |
| ESLint + Prettier | **ruff** (lint + format) |
| tsc | mypy / pyright |
| Jest / Vitest | pytest |
| Express / Nest | FastAPI / Flask / Django |
| Prisma / Drizzle | SQLAlchemy / SQLModel / Django ORM |
| zod | Pydantic |
| nodemon | `uvicorn --reload` / `fastapi dev` |
