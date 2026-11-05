# C1 · Capstone: Task Tracker API

> Build a multi-user task tracker, the kind of backend a React app (or a take-home assignment) would use. It combines everything: Pydantic contracts, SQLAlchemy relationships, JWT auth, **resource-level authorization**, filtering, sorting and pagination, and correct status codes.

```bash
python check.py c1              # acceptance tests (capstone/test_c1.py is the source of truth)
python run.py c1                # → http://127.0.0.1:8000/docs  (use "Authorize" after registering)
python run.py c1 --solution
```

## What's provided (`exercise/`)
| File | State |
|---|---|
| `database.py`, `security.py`, `deps.py` (`DB`, `CurrentUser`), `main.py` | ✅ done |
| `routers/auth.py`: register, token, `/users/me` | ✅ done. Read it as a worked example |
| `models.py` | `User` + `project_members` done. Finish `Project`, write `Task` |
| `schemas.py` | user schemas done. Write the project and task schemas |
| `access.py` | write the authorization helpers |
| `routers/projects.py`, `routers/tasks.py` | write them |

## 📜 Spec
Every endpoint except `/auth/*` and `/health` requires `Authorization: Bearer <token>` (401).

### Authorization rules
- Only project **members** can see a project or its tasks. Everyone else gets **404**, not 403, so they can't tell it exists.
- Only the project **owner** can update or delete the project and manage members (**403** for other members).
- A task can be deleted by its **creator** or the project **owner** (403 for other members).
- A task's assignee must be a member of the project (**422**).

### Projects
| Endpoint | Behaviour |
|---|---|
| `POST /projects` `{name (1–100), description? (≤2000, default "")}` | 201 + `Location`. Creator = owner, automatically a member. Unknown fields → 422 |
| `GET /projects` | the projects I'm a member of, ordered by id → `[ProjectOut]` |
| `GET /projects/{id}` | `ProjectOut {id, name, description, owner_id, members: [{id, email, name}]}` (members ordered by id) |
| `PATCH /projects/{id}` | owner only. Partial update |
| `DELETE /projects/{id}` | owner only. 204. Its tasks are deleted too |
| `POST /projects/{id}/members` `{email}` | owner only. 201 → ProjectOut. Unknown email 404, already a member 409 |
| `DELETE /projects/{id}/members/{user_id}` | owner only. 204. The owner can't be removed (422), a non-member gives 404. Their tasks **in this project** become unassigned |

### Tasks
| Endpoint | Behaviour |
|---|---|
| `POST /projects/{id}/tasks` | `{title (1–200), description?, status? ("todo"\|"in_progress"\|"done", default todo), priority? ("low"\|"medium"\|"high", default medium), due_date? (YYYY-MM-DD), assignee_id?}` → 201 + `Location: /tasks/{id}` |
| `GET /projects/{id}/tasks` | filters `status`, `priority`, `assignee_id`, `q` (title/description contains); `sort` (comma list of `due_date`, `priority`, `created_at`, `title`, `-` = desc, default `created_at`, unknown field → 422; `due_date` puts nulls last; priority sorts low < medium < high); `limit` (1–100, default 20), `offset` → `{items, total, limit, offset}`. Always break ties by id |
| `GET /tasks/{id}` | `TaskOut {id, project_id, title, description, status, priority, due_date, assignee_id, created_by_id, created_at, completed_at}` |
| `PATCH /tasks/{id}` | any member. Partial. Setting status to `done` sets `completed_at`, and moving away from `done` clears it |
| `DELETE /tasks/{id}` | creator or project owner. 204 |
| `GET /me/tasks` | tasks assigned to me across all projects. `status` filter, `sort` (default `due_date`), pagination |

## Suggested order
1. Models → `access.py` → projects (create, list, get) → membership → tasks CRUD → list filters → sorting → `/me/tasks`.
2. Run `python check.py c1 -v` often. The test names map to spec sections.
3. Then compare with `solution/`, especially `access.py`, the `case(...)` priority sort, and the single `UPDATE` that unassigns a removed member's tasks.

## Stretch goals (not graded)
- Alembic migrations instead of `create_all` (F08).
- Comments on tasks (`/tasks/{id}/comments`) with an N+1-free list.
- ETags plus `If-Match` on `PATCH /tasks/{id}` (F15).
- Cursor pagination for `/me/tasks` (drill D2).
- An activity log written by a background task (F13), and a WebSocket that pushes task updates to project members (F14).
- Swap to Postgres + asyncpg with async SQLAlchemy (F12).
- Generate a TS client from `/openapi.json` and wire up a small React UI.

## 💼 How to present this in an interview
"It's a layered FastAPI service. Thin routers, an authorization module enforcing membership and ownership with 404-not-403 semantics, SQLAlchemy 2.0 with eager loading, Pydantic contracts with `extra=forbid`, JWT with pinned algorithms and Argon2, whitelisted sorting, envelope pagination, and an acceptance suite with DB-per-test isolation. Next I'd add migrations, Postgres, rate limiting on `/auth/token`, observability, and cursor pagination."
