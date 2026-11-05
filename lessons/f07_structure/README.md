# F07 · `APIRouter`, project layout, settings

> One `main.py` works for a demo but doesn't last on a team. Real FastAPI projects split by **feature** (routers), keep config **typed and validated** (pydantic-settings), and keep `main.py` for assembly only.

## 🧠 Concepts

### A layout that scales
```
app/
  main.py            # create_app(): FastAPI(), middleware, include_router(...)
  config.py          # Settings(BaseSettings) + get_settings()
  db.py              # engine, session dependency                 [F08]
  deps.py            # shared dependencies: CurrentUser, DB, PageDep
  routers/           # HTTP layer, thin: parse → call service → shape response
    books.py
    authors.py
  services/          # business logic, no HTTP (raises domain errors)  [F05]
  models.py          # SQLAlchemy tables
  schemas.py         # Pydantic request/response models
tests/
```
Some teams go "package by feature" instead (`books/router.py`, `books/service.py`, `books/schemas.py`). Either is fine, as long as it's consistent.

### APIRouter = Express Router
```python
router = APIRouter(prefix="/books", tags=["books"])

@router.get("")              # → /books   (empty string avoids a /books/ redirect)
@router.get("/{book_id}")    # → /books/{book_id}

app.include_router(router, prefix="/api/v1")           # → /api/v1/books
app.include_router(admin.router, dependencies=[Depends(require_admin)])
```

### Settings with pydantic-settings
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOOKSHELF_", env_file=".env")
    app_name: str = "Bookshelf"
    debug: bool = False                 # "true"/"1"/"yes" → True
    database_url: str = "sqlite:///./app.db"
    secret_key: SecretStr               # required: startup fails if it's missing (fail fast!)

@lru_cache
def get_settings() -> Settings: return Settings()

def info(settings: Annotated[Settings, Depends(get_settings)]): ...   # injectable and overridable
```
- Precedence: init kwargs > env vars > `.env` file > defaults.
- `SecretStr` hides the value in logs and reprs (`.get_secret_value()` to read it).
- Fail fast: a typo'd or missing env var should crash at boot, not at 3am on the first request that needs it.

### The app factory
`create_app()` builds and returns the app. Tests and scripts can then build variants (other settings) without import-time side effects.

## 🏋️ Exercise
Refactor the monolithic `exercise/main.py` (the tests describe the target):
1. `config.py`: `Settings` with `env_prefix="BOOKSHELF_"`, `app_name="Bookshelf"`, `debug=False`, `max_page_size=50`, and an `@lru_cache` `get_settings()`.
2. `routers/books.py` (`prefix="/books"`, tag `books`), `routers/authors.py` (`/authors`, `authors`), and `routers/meta.py` (no prefix, tag `meta`, `GET /info` using `Depends(get_settings)`).
3. `main.py`: include every router under `/api/v1`. No endpoints defined in `main.py`.

```bash
python check.py f07
```

## 💼 Interview angle
- *"How do you structure a large FastAPI app?"*: routers per feature, a service layer for business logic, separate Pydantic schemas and ORM models, shared deps, and an app factory.
- *"How do you manage configuration and secrets?"*: env vars validated by pydantic-settings at boot, `SecretStr`, `.env` only for local dev, and a secret manager (AWS SM, Vault, Doppler) in production.
- *"How do you version an API?"*: a URL prefix (`/api/v1`) through `include_router`, a header or media type, or additive non-breaking changes plus deprecation (F15).
- *"Why `@lru_cache` on get_settings?"*: it parses the env once, gives a singleton without a global, and it can still be overridden in tests.
