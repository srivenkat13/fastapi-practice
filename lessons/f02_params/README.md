# F02 · Path & query parameters, validation

> FastAPI decides where each parameter comes from by looking at your function signature: names that appear in the path are **path params**, and other simple types are **query params**. `Annotated[..., Path()/Query()]` adds validation and docs.

## 🧠 Concepts

```python
from typing import Annotated
from enum import Enum
from fastapi import FastAPI, Path, Query, HTTPException

@app.get("/books/{book_id}")
def get_book(book_id: Annotated[int, Path(gt=0, description="Book ID")]):
    ...                                    # "abc" or 0 → automatic 422

@app.get("/books")
def list_books(
    q: str | None = None,                                  # optional: ?q=python
    genre: Genre | None = None,                            # Enum: only allowed values
    min_year: Annotated[int | None, Query(ge=1450)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,        # validated, and documented in /docs
    offset: Annotated[int, Query(ge=0)] = 0,
    tags: Annotated[list[str], Query(alias="tag")] = [],   # ?tag=a&tag=b (lists need Query())
): ...
```
- **Type conversion**: `"42"` → `42`, `"true"`/`"1"`/`"yes"` → `True`. Invalid input gets a **422 Unprocessable Content** with details. You write no parsing code.
- `str`-based `Enum` params show up as a dropdown in `/docs` and give you exhaustiveness.
- Validators: `gt ge lt le` for numbers, and `min_length max_length pattern` for strings.
- `alias` maps an external name (such as `tag`, or `X-Foo` for headers) to your Python name.
- Raise `HTTPException(status_code=404, detail="Book not found")` for "valid input, but no such resource". Lesson F05 goes deeper.

### ⚠️ Route order matters
Routes are matched **in declaration order**. If `/books/{book_id}` is declared before `/books/featured`, then `GET /books/featured` matches the first route, `"featured"` fails the `int` check, and you get a **422** instead of your featured list. Declare fixed paths before parameterized ones.

### `Annotated` vs default-value style
Older code writes `limit: int = Query(10, ge=1)`. The docs now recommend `Annotated[int, Query(ge=1)] = 10`. It keeps the real default as a real Python default, and you can reuse the type as an alias:
```python
PageLimit = Annotated[int, Query(ge=1, le=50)]
```

## 🏋️ Exercise
`exercise/main.py` has an in-memory `BOOKS` list. Make the tests pass:
1. `GET /books/{book_id}`: `book_id` must be > 0. Return 404 `{"detail": "Book not found"}` when it doesn't exist.
2. `GET /books/featured`: currently returns 422 because of route order. Fix it.
3. `GET /books` filters: `q` (case-insensitive title substring), `genre` (the `Genre` enum), `min_year` (≥ 1450), repeatable `tag` (the book must have **all** of them), then `offset`/`limit` (limit 1–50, default 10).
4. `GET /genres/{genre}/count`: `genre` is a `Genre` path param; return `{"genre": ..., "count": n}`.

```bash
python check.py f02          # then: python run.py f02 → /docs
```

## 💼 Interview angle
- *"Path vs query parameter: when do you use each?"*: path identifies a resource (`/books/42`). Query filters, sorts or paginates a collection (`/books?genre=tech&limit=10`).
- *"What status code for invalid input?"*: 422 (FastAPI's default for a schema violation) or 400 for a malformed request. Be consistent and document it.
- *"Why might `/users/me` return 422?"*: route order. `/users/{id: int}` matched first.
- *"How does FastAPI know `limit` is a query param?"*: it's not in the path template and it's a simple type, so it's a query param. Pydantic models default to the body.
