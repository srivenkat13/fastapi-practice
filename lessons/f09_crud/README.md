# F09 · CRUD, pagination, filtering, sorting

> Nearly every backend interview task is some version of this lesson: a resource with create, read, update and delete, plus a list endpoint that filters, sorts and paginates **correctly**. "Correctly" means the total respects the filters, sorting is whitelisted, and pages are stable.

## 🧠 Concepts

### Layering
```
main.py (HTTP)   → validates input, maps errors to status codes, shapes responses
crud.py (data)   → SQLAlchemy queries, raises domain errors (DuplicateISBN)
models / schemas → storage vs contract
```
`main.py` is already written. Read it first, because it shows the "thin router" style. A dependency `book_or_404` loads the resource once and is reused by GET, PUT, PATCH and DELETE.

### REST conventions
| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/books` | 201 + `Location` | 409 duplicate, 422 invalid |
| GET | `/books` | 200 page envelope | 422 bad params |
| GET | `/books/{id}` | 200 | 404 |
| PUT | `/books/{id}` | 200 (full replace; all fields required) | 404, 409, 422 |
| PATCH | `/books/{id}` | 200 (partial, `exclude_unset`) | 404, 422 |
| DELETE | `/books/{id}` | 204 | 404 |

### Pagination done right
```python
base = filters.apply(select(Book))
total = db.scalar(select(func.count()).select_from(base.subquery()))   # count with the SAME filters
page = base.order_by(*order_by, Book.id).limit(limit).offset(offset)  # id = tie-breaker → stable pages
```
- **Offset pagination** (`?limit=20&offset=40`) is simple and supports jumping to page N, but it gets slow on deep pages, and rows shift if data changes between requests.
- **Cursor/keyset pagination** (`?after=<opaque cursor>`, `WHERE (year, id) < (:y, :id)`) is fast and stable, which suits feeds and infinite scroll. You'll build one in drill D2.

### Sorting safely
Never pass user input to `order_by(text(sort))`, because that's SQL injection. Parse `sort=-year,title` against a **whitelist** and map it to column objects.

### Search
`Book.title.ilike(f"%{q}%")` is parameterised, so it's safe. A leading `%` can't use a B-tree index, so at scale use Postgres full-text search (`tsvector`), trigram indexes (`pg_trgm`), or a search engine.

## 🏋️ Exercise
Implement every function in `exercise/crud.py` (`parse_sort`, `create_book`, `get_book`, `list_books`, `update_book`, `delete_book`).
```bash
python check.py f09
```

## 💼 Interview angle
- *"Offset vs cursor pagination?"*: offset allows random access but is O(offset) on deep pages and unstable under writes. A cursor is O(1) with an index and stable, but you can only go next or prev.
- *"How do you implement sorting by user-chosen fields safely?"*: a whitelist mapped to columns, plus a unique tie-breaker.
- *"PUT vs PATCH, and idempotency?"*: PUT replaces and is idempotent. PATCH is partial and not necessarily idempotent (`{"op": "increment"}`). DELETE is idempotent in effect (a second call gives 404, but the state is the same).
- *"How do you return a 409 vs a 422?"*: 422 means the request is malformed by itself. 409 means it conflicts with current state (a unique constraint, or a version mismatch).
- *"Why does `total` need the same filters?"*: so the UI's "Showing 1–20 of N" is right. It's a common bug.
