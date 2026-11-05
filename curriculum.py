"""The lesson registry used by check.py, progress.py and run.py."""

TRACKS = {
    "python": "P · Python refresher (for JS/TS developers)",
    "fastapi": "F · FastAPI core",
    "real": "R · Real-world backend",
    "capstone": "C · Capstone",
    "drills": "D · Interview drills (timed)",
}

# id, track, folder, title, app (module path for `python run.py <id>`, or None)
UNITS = [
    ("p1", "python", "lessons/p1_basics", "Values, strings, truthiness, None", None),
    ("p2", "python", "lessons/p2_collections", "Lists, dicts, sets, tuples, comprehensions", None),
    ("p3", "python", "lessons/p3_functions", "Functions, *args/**kwargs, closures, decorators", None),
    ("p4", "python", "lessons/p4_classes", "Classes, dataclasses, exceptions, context managers", None),
    ("p5", "python", "lessons/p5_modules", "Modules, packages, imports, venvs", None),
    ("p6", "python", "lessons/p6_typing", "Type hints in depth (FastAPI runs on these)", None),
    ("p7", "python", "lessons/p7_generators", "Iterators, generators, yield", None),
    ("p8", "python", "lessons/p8_async", "async/await and the event loop", None),
    ("f01", "fastapi", "lessons/f01_first_app", "First app, /docs, request lifecycle", "main:app"),
    ("f02", "fastapi", "lessons/f02_params", "Path & query parameters, validation", "main:app"),
    ("f03", "fastapi", "lessons/f03_bodies", "Request bodies with Pydantic v2", "main:app"),
    ("f04", "fastapi", "lessons/f04_responses", "Response models, status codes, DTOs", "main:app"),
    ("f05", "fastapi", "lessons/f05_errors", "Errors & consistent error shapes", "main:app"),
    ("f06", "fastapi", "lessons/f06_dependencies", "Dependency injection with Depends", "main:app"),
    ("f07", "fastapi", "lessons/f07_structure", "APIRouter, project layout, settings", "main:app"),
    ("f08", "fastapi", "lessons/f08_database", "SQLAlchemy 2.0 + SQLite, sessions", "main:app"),
    ("f09", "fastapi", "lessons/f09_crud", "CRUD, pagination, filtering, sorting", "main:app"),
    ("f10", "fastapi", "lessons/f10_auth", "Auth: hashing, JWT, current user, roles", "main:app"),
    ("f11", "fastapi", "lessons/f11_testing", "Testing: TestClient, overrides, fixtures", "main:app"),
    ("f12", "fastapi", "lessons/f12_async", "Async in practice: def vs async def", "main:app"),
    ("f13", "fastapi", "lessons/f13_middleware", "Middleware, CORS, lifespan, background tasks", "main:app"),
    ("f14", "fastapi", "lessons/f14_files_streaming", "Uploads, streaming, WebSockets", "main:app"),
    ("f15", "fastapi", "lessons/f15_rest_design", "REST design: versioning, ETags, idempotency, rate limits", "main:app"),
    ("r1", "real", "lessons/r1_flask_compare", "Flask vs FastAPI: the same API twice", None),
    ("r2", "real", "lessons/r2_caching", "Caching (Redis-style, in-memory backend)", "main:app"),
    ("r3", "real", "lessons/r3_observability", "Logging, request IDs, health checks", "main:app"),
    ("r4", "real", "lessons/r4_deployment", "Production config, Docker, workers", "main:app"),
    ("c1", "capstone", "capstone", "Task Tracker API", "main:app"),
    ("d1", "drills", "drills/d1_rate_limiter", "Drill: rate-limit dependency (25 min)", "main:app"),
    ("d2", "drills", "drills/d2_search_endpoint", "Drill: search + cursor pagination (30 min)", "main:app"),
    ("d3", "drills", "drills/d3_fix_the_bugs", "Drill: debug a broken API (25 min)", "main:app"),
    ("d4", "drills", "drills/d4_idempotent_payments", "Drill: idempotent payments (30 min)", "main:app"),
]


def find(unit_id: str):
    key = unit_id.lower().strip()
    if key.isdigit():  # "5" or "05" -> f05
        key = f"f{int(key):02d}"
    for unit in UNITS:
        if unit[0] == key:
            return unit
    raise SystemExit(f"Unknown lesson '{unit_id}'. Try one of: {', '.join(u[0] for u in UNITS)}")
