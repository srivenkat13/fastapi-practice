# Live coding & take-home playbook

## Formats you'll meet for a Python backend role
| Format | Length | Practise with |
|---|---|---|
| "Build a small API" (CRUD + one twist) | 45–60 min | F09, C1, D2 |
| "Add X to this codebase" (rate limiting, caching, auth) | 30–45 min | D1, R2, F10 |
| "Debug this service" | 20–30 min | D3 |
| "Design the API, then implement one endpoint" | 60 min | system-design.md + F15/D4 |
| Take-home (2–4 h, graded on quality) | async | the capstone |
| Python fundamentals (data structures, comprehensions, generators) | 20–30 min | P1–P8 |

## The 60-minute "build an API" script
1. **(3 min) Clarify**: resources, fields, rules, auth? persistence? pagination? Say your assumptions out loud.
2. **(5 min) Contract first**: write the Pydantic schemas and route signatures with status codes. Interviewers love seeing the contract before any logic.
3. **(25 min) Implement the happy path**, one endpoint at a time, and **test as you go** with TestClient (F11). One quick test per endpoint is enough.
4. **(15 min) Edge cases**: 404s, validation, duplicates (409), authorization, pagination bounds.
5. **(5 min) Wrap up**: what you'd add with more time: DB migrations, auth, rate limiting, observability, cursor pagination, caching.

## Habits that score points
- Talk while you type: "I'm returning 201 with a Location header because…"
- Small commits, and run the tests often.
- Use `Annotated` + `Depends` for anything reusable (pagination, current user, DB).
- Separate input, output and DB models. Use `response_model` and `extra="forbid"`.
- Name the trade-off when you take a shortcut: "In-memory dict for now; in production this is Postgres with a unique index on email."
- When stuck, simplify: get something working, then improve it.

## Take-home checklist (the capstone already covers most of this)
- [ ] README: how to run, design decisions, trade-offs, what's next
- [ ] Clear structure (routers / services / schemas / models)
- [ ] Tests that run with one command, including auth and edge cases
- [ ] Consistent error format, correct status codes
- [ ] Config via env, no secrets committed
- [ ] Type hints throughout, linted and formatted (`ruff check`, `ruff format`)
- [ ] Migrations, or at least an explanation of why not
- [ ] Optional extras: Dockerfile, a CI workflow, a seed script, an OpenAPI tour

## Timed practice plan
Repeat each drill until you finish **under time** without peeking. Then explain the solution's design in 2 minutes, recorded on your phone. Uncomfortable, but very effective.

| Week | Drills |
|---|---|
| 1 | D3 (debug) → D1 (rate limiter) |
| 2 | D2 (cursor pagination) → D4 (idempotency) |
| 3 | Rebuild F09 from scratch in 45 min without notes. Rebuild C1's projects module in 60 min |
