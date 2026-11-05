# FastAPI Practice: learn Python + REST APIs lesson by lesson

A hands-on course for a **React/TS developer** that refreshes Python, teaches FastAPI properly, and prepares you for **backend / Python interviews**. Every unit has concepts (with JS comparisons), an exercise, a reference solution, automated checks, and an **interview angle**.

## Setup (once)
```bash
cd ~/Code/personal/fastapi-practice
source .venv/bin/activate          # Python 3.11 venv (pyenv). Already created, with dependencies installed.
# re-creating it from scratch:
#   ~/.pyenv/versions/3.11.9/bin/python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```
No databases or services to install. SQLite and in-memory fakes cover everything.

## Daily loop
```bash
python progress.py               # what's done, what's next
open lessons/p1_basics/README.md # read the concepts, then edit the exercise file(s)
python check.py p1               # grade it (add -v for full tracebacks)
python run.py f03                # run a lesson's API → http://127.0.0.1:8000/docs
python check.py f03 --solution   # check the reference solution passes
```
Lesson IDs: `p1`…`p8`, `f01`…`f15` (or just `5` for f05), `r1`…`r4`, `c1`, `d1`…`d4`.

## Curriculum

### P · Python refresher (do these first if your Python is rusty)
| | Topic | You build |
|---|---|---|
| P1 | values, strings, truthiness, `None` | string and number utilities |
| P2 | lists, dicts, sets, comprehensions, `collections` | API-style data transforms |
| P3 | `*args/**kwargs`, closures, **decorators** | `@retry`, `@memoize`, a mini `@app.get` |
| P4 | classes, dataclasses, exceptions, **context managers** | a wallet with transactions |
| P5 | modules, packages, imports, venvs | fix a broken package |
| P6 | **type hints** in depth, `Annotated` | a toy FastAPI that validates from type hints |
| P7 | iterators, **generators**, `yield` | a lazy paginator, yield-dependency semantics |
| P8 | **async/await**, gather, semaphores, timeouts | concurrent fetchers (timing-tested) |

### F · FastAPI core
| | Topic |
|---|---|
| F01 | first app, `/docs`, ASGI, request lifecycle |
| F02 | path and query params, validation, route order |
| F03 | Pydantic v2 bodies, validators, PATCH semantics |
| F04 | response models (DTOs), status codes, envelopes |
| F05 | domain exceptions, one error envelope, safe 500s |
| F06 | **dependency injection**: yield deps, guards, factories, overrides |
| F07 | APIRouter, project layout, pydantic-settings |
| F08 | SQLAlchemy 2.0 + SQLite, relationships, **N+1** (query-counted) |
| F09 | full CRUD, filtering, whitelisted sorting, pagination |
| F10 | auth: Argon2, JWT (pinned algorithms), OAuth2 flow, roles |
| F11 | testing, **graded by mutation testing**: your tests must catch 6 planted bugs |
| F12 | async in practice: `def` vs `async def`, fan-out, timeouts, async DB |
| F13 | middleware, CORS, lifespan, background tasks, GZip |
| F14 | uploads (magic bytes), streaming CSV, SSE, WebSocket rooms |
| F15 | REST design: versioning, ETags/If-Match, idempotency keys, rate limits, OpenAPI |

### R · Real-world backend
| | Topic |
|---|---|
| R1 | **Flask vs FastAPI**: rebuild an API in Flask (app factory, blueprints, `g`), with a parity test |
| R2 | caching: cache-aside, TTL, invalidation, negative caching, **stampede protection**, HTTP caching |
| R3 | observability: JSON logs, request IDs via `contextvars`, liveness and readiness |
| R4 | production config that fails fast, security headers, Dockerfile review |

### C · Capstone: Task Tracker API
Users, JWT auth, projects with members, tasks with filters, sorting and pagination, and resource-level authorization. See [capstone/README.md](capstone/README.md).

### D · Timed interview drills
| | Drill | Time |
|---|---|---|
| D1 | rate-limit dependency (sliding window) | 25 min |
| D2 | search + cursor pagination | 30 min |
| D3 | debug a broken API (7 bugs) | 25 min |
| D4 | idempotent payments (concurrent duplicates!) | 30 min |

### Interview prep → [interview/](interview/README.md)
A question bank (~80 Q&As tagged by lesson), a JS→Python cheat sheet, FastAPI vs Flask vs Django, system-design scenarios, and a live-coding playbook.

## Suggested schedule (~5–6 weeks at 1–1.5 h/day)
| Week | Work |
|---|---|
| 1 | P1–P8 (Python is coming back) + interview/python-for-js-devs.md |
| 2 | F01–F07 (FastAPI fundamentals) |
| 3 | F08–F12 (data, auth, testing, async) |
| 4 | F13–F15, R1–R4 |
| 5 | Capstone |
| 6 | Drills D1–D4 under time + question bank out loud + one system-design rehearsal |

## How grading works
- Each unit has `exercise/` (yours) and `solution/` (reference). Tests import your code through `support.target()`, and `--solution` / `SOLUTIONS=1` points them at the reference instead.
- API lessons are tested over HTTP with FastAPI's `TestClient` / `httpx.AsyncClient`. Some lessons also check **timing** (async), **query counts** (N+1), **log records** (R3), or **your own tests** (F11, by mutation testing).
- Run everything at once: `python -m pytest` (exercises) or `SOLUTIONS=1 python -m pytest` (solutions should all pass).

## Flask or FastAPI?
FastAPI for learning REST API building today: types drive validation and docs, it's async-native, and DI keeps code testable. R1 covers Flask so you can read and maintain Flask codebases too. The full comparison is in [interview/framework-comparison.md](interview/framework-comparison.md).

## Repo layout
```
check.py / progress.py / run.py   CLI helpers          curriculum.py   lesson registry
support/                          test helper (exercise vs solution)
lessons/<id>_<topic>/             README.md, exercise/, solution/, test_<id>.py
capstone/  drills/  interview/
```
