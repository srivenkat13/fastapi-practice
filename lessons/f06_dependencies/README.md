# F06 · Dependency injection with `Depends`

> `Depends` is FastAPI's main architectural tool. A dependency is **any callable whose parameters FastAPI resolves the same way it resolves an endpoint's**. Use dependencies for DB sessions, the current user, pagination, permissions, settings and HTTP clients. Tests swap them with `app.dependency_overrides`.

## 🧠 Concepts

### Function dependencies (shared parameter parsing)
```python
@dataclass
class Pagination:
    limit: int
    offset: int

def pagination(limit: Annotated[int, Query(ge=1, le=100)] = 20,
               offset: Annotated[int, Query(ge=0)] = 0) -> Pagination:
    return Pagination(limit, offset)

PageDep = Annotated[Pagination, Depends(pagination)]      # reusable alias

@app.get("/books")
def list_books(page: PageDep): ...            # limit and offset still appear in /docs
```

### `yield` dependencies (setup → request → teardown)
```python
def get_db():
    db = SessionLocal()
    try:
        yield db          # injected into the endpoint
    finally:
        db.close()        # runs after the response is sent, even if the endpoint raised
```
Newer FastAPI versions let you choose when the teardown runs: `Depends(get_db, scope="function")` closes the resource **right after the endpoint returns**, before the response goes out. The default `"request"` scope tears down after the response has been sent. Use `"function"` to release DB connections early, and avoid it when a `StreamingResponse` still needs the resource.

### Sub-dependencies and per-request caching
```python
def get_token(authorization: Annotated[str | None, Header()] = None) -> str: ...
def get_current_user(token: Annotated[str, Depends(get_token)], db: DB) -> User: ...
def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User: ...
```
FastAPI resolves the graph. If two dependencies need `get_current_user`, it runs **once per request** and the value is cached (`Depends(fn, use_cache=False)` to opt out).

### Dependencies without a value: guards
```python
def require_api_key(x_api_key: Annotated[str | None, Header()] = None):
    if x_api_key != "secret": raise HTTPException(401, "Invalid API key")

admin = APIRouter(prefix="/admin", dependencies=[Depends(require_api_key)])  # every route is guarded
app = FastAPI(dependencies=[...])                                            # or globally
```
Headers: the parameter `x_api_key` maps to the `x-api-key` header automatically (underscores become hyphens).

### Class dependencies and dependency factories
```python
class Filters:                                         # a class is a callable too
    def __init__(self, q: str | None = None, genre: str | None = None): ...

def require_role(role: str):                           # factory → closure (see P3)
    def checker(user: CurrentUser) -> User:
        if role not in user.roles: raise HTTPException(403)
        return user
    return checker

@app.delete("/books/{id}", dependencies=[Depends(require_role("admin"))])
```

### Testing: override anything
```python
app.dependency_overrides[get_db] = lambda: fake_db
app.dependency_overrides[get_current_user] = lambda: User(id=1, roles=["admin"])
```

## 🏋️ Exercise
`exercise/main.py` copy-pastes pagination, opens a "DB" without closing it, and checks the API key by hand in each admin route.
1. `pagination()` dependency + `PageDep` alias, used by `/books` and `/authors`.
2. `get_db()` as a `yield` dependency that **always** closes the DB, even when the endpoint raises.
3. `require_api_key` guard applied to the whole `admin` router (`X-API-Key: letmein`, else 401).
4. `get_current_user` reads the `X-User` header (401 if missing), and `require_role(role)` is a factory giving 403. Wire it into `DELETE /books/{id}` (role `admin`).
5. `/whoami` uses `get_current_user` **twice** (directly and through `audit_user`). It must only run once per request.

```bash
python check.py f06
```

## 💼 Interview angle
- *"What is dependency injection in FastAPI and why use it?"*: declaring what an endpoint needs instead of building it. You get reuse, a composable auth and permission graph, per-request caching, cleanup via yield, and easy test overrides.
- *"How does FastAPI clean up a DB session?"*: with a `yield` dependency. The code after `yield` runs after the response is sent, and errors are re-raised at the yield.
- *"How do you apply auth to a whole group of routes?"*: `APIRouter(dependencies=[Depends(...)])` or `include_router(..., dependencies=...)`.
- *"Is a dependency called twice if two parts of the graph need it?"*: no. It's cached per request unless `use_cache=False`.
- *"How do you mock the database in tests?"*: `app.dependency_overrides[get_db] = ...`. No monkeypatching of globals needed.
