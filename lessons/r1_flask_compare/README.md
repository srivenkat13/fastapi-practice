# R1 · Flask vs FastAPI: the same API, built twice

> You picked FastAPI, but plenty of production Python runs on **Flask** (and Django). Rebuilding one API in Flask shows you what FastAPI gives you for free, and makes a Flask codebase readable when you inherit one.

## 🧠 Concepts

### Side by side
| Concern | FastAPI | Flask |
|---|---|---|
| Protocol | ASGI (async-native) | WSGI (sync. `async def` views work, but each one still occupies a worker) |
| Routing | `@app.get("/books/{id}")` | `@app.get("/books/<int:id>")` (Flask 2+) or `@app.route(..., methods=[...])` |
| Grouping | `APIRouter` | `Blueprint` |
| Path params | type hints → validated | URL converters (`<int:id>`): a mismatch is a **404**, not a 422 |
| Query | function params | `request.args.get("q")` (strings, so you parse them) |
| Body | Pydantic model → 422 with details | `request.get_json()` + validation by hand (or marshmallow, or pydantic) |
| Response | return a dict/model, `response_model` filters it | return a dict/`jsonify`, or a `(body, status)` tuple |
| DI | `Depends` | none: **context globals** `request`, `g` (per-request), `current_app`, `session` |
| Middleware | `@app.middleware` / ASGI | `before_request` / `after_request` hooks, WSGI middleware |
| Errors | `exception_handler` | `@app.errorhandler(404 or Exception)` |
| Config | pydantic-settings | `app.config` (dict-like, `from_object`, `from_prefixed_env`) |
| Docs | built-in OpenAPI | add-ons (flask-smorest, apiflask, flasgger) |
| Server | uvicorn | gunicorn (sync workers, or gevent for many I/O connections) |
| Ecosystem | young, API-focused | mature: Flask-Login, Flask-SQLAlchemy, Flask-Migrate, Jinja templates |

### Flask idioms you need to recognise
```python
def create_app(config=None):          # the APP FACTORY: the standard Flask pattern
    app = Flask(__name__)
    app.config.update(config or {})
    db.init_app(app)                  # extensions bind late, so one extension instance serves many apps
    app.register_blueprint(books_bp, url_prefix="/books")
    return app

from flask import g, current_app, request
g.user = ...                          # per-request scratch space
current_app.config["API_KEY"]         # the app handling this request (a context-local proxy)
```
Flask's **context locals** (`request`, `g`, `current_app`) are thread-local proxies. They're convenient, but they're implicit global state. Accessing them outside a request raises "Working outside of application context". FastAPI's explicit DI replaces all of these.

### When would you still choose Flask?
- An existing Flask codebase or team expertise, server-rendered pages with Jinja, or a plugin ecosystem you depend on.
- Django is the pick for batteries-included admin, auth and ORM in a CRUD-heavy product. Django Ninja gives FastAPI-style APIs on Django.

## 🏋️ Exercise
Rebuild `fastapi_app.py` in `exercise/flask_app.py`, following the requirements in its docstring: an app factory, a blueprint, validation by hand, JSON errors, and request IDs through `g`. A **parity test** sends the same requests to both apps.
```bash
python check.py r1
flask --app lessons.r1_flask_compare.exercise.flask_app:create_app run --port 5001
```
As you write the validation by hand, notice how much Pydantic was doing for you.

## 💼 Interview angle
- *"Flask or FastAPI for a new service?"*: FastAPI for an API-first service: types drive validation and docs, async I/O, and DI. Flask when the team or ecosystem is there, or for server-rendered apps. Django for a full-stack product with an admin.
- *"What are Flask's application and request contexts?"*: context-local proxies (`current_app`, `g`, `request`) that are pushed per request. That's why you need `app.app_context()` in scripts and tests.
- *"How do you scale a Flask app?"*: gunicorn with N sync workers (about 2×cores+1), or gevent/eventlet workers for I/O-heavy loads, behind nginx, with horizontal pods.
- *"Why the app factory pattern?"*: several configurations (test or prod), no import-time side effects, and extensions initialised once per app.
