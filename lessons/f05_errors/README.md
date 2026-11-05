# F05 · Errors and consistent error shapes

> Out of the box, FastAPI returns three different error shapes: `{"detail": "..."}` from `HTTPException`, `{"detail": [ {...} ]}` from validation, and plain-text 500s. A senior-level API has **one error envelope**, **domain exceptions** that know nothing about HTTP, and **no stack traces sent to clients**.

## 🧠 Concepts

### Domain exceptions + one translation layer
```python
class AppError(Exception):
    status_code = 400
    code = "app_error"
    def __init__(self, message: str): self.message = message

class NotFound(AppError):  status_code, code = 404, "not_found"
class Conflict(AppError):  status_code, code = 409, "conflict"

# services raise domain errors (they're reusable from CLIs, workers and tests)
def reserve(book_id): raise OutOfStock(f"Book {book_id} is out of stock")

@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code,
                        content={"error": {"code": exc.code, "message": exc.message}})
```

### Override the built-in handlers
```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(RequestValidationError)   # the 422s
async def on_validation(request, exc):
    details = [{"field": ".".join(map(str, e["loc"][1:])), "message": e["msg"]} for e in exc.errors()]
    ...

@app.exception_handler(StarletteHTTPException)   # HTTPException and unknown routes (404/405)
async def on_http(request, exc): ...

@app.exception_handler(Exception)                # anything unexpected → a generic 500
async def on_crash(request, exc):
    logger.exception("unhandled")                 # log the details on the server...
    return JSONResponse(500, {"error": {"code": "internal_error", "message": "Something went wrong"}})  # ...not to the client
```
> Register the `HTTPException` handler for **Starlette's** class. FastAPI's `HTTPException` subclasses it, and Starlette raises its own for unknown routes.

### Error envelope design (RFC 9457 "Problem Details" is the standard version)
```json
{ "error": { "code": "out_of_stock", "message": "Book 2 is out of stock", "details": [] } }
```
- A machine-readable `code` (the frontend switches on it) and a human `message`.
- `details` for field-level errors (form highlighting).
- The same shape on every status code. Never send stack traces, SQL, or internal IDs.

## 🏋️ Exercise
`exercise/main.py` has a small bookstore with `reserve` and `get` endpoints. Make every error use the envelope `{"error": {"code", "message", "details"}}`:
1. Define `AppError` → `NotFound` (404, `not_found`) and `OutOfStock` (409, `out_of_stock`), and raise them from the service functions.
2. Handlers for `AppError`, `RequestValidationError` (422, `validation_error`, details `[{"field", "message"}]`), Starlette `HTTPException` (`code` = `"http_<status>"`), and `Exception` (500, `internal_error`, generic message).

```bash
python check.py f05
```

## 💼 Interview angle
- *"How do you structure error handling in an API?"*: domain exceptions in the service layer, mapped to HTTP in one place, with a consistent envelope, logged with a request ID (R3), and nothing internal leaked.
- *"Why not raise `HTTPException` from the service layer?"*: it couples business logic to HTTP. The same service might be called from a CLI, a worker or tests.
- *"What's RFC 9457 (formerly 7807)?"*: the standard `application/problem+json` format (`type`, `title`, `status`, `detail`, `instance`).
- *"How should a 500 look?"*: a generic message and a correlation ID. Full details go to logs and Sentry, never to the client.
