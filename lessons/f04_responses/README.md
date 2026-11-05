# F04 · Response models, status codes, DTOs

> Input validation is half the contract. The other half is **what you send back**. A response model filters your return value down to an allowed set of fields, so an internal `password_hash` can't leak even if you return the whole DB object. This is the API version of "send DTOs, not DB rows".

## 🧠 Concepts

### `response_model` (or a return annotation)
```python
class UserInDB(BaseModel):            # internal
    id: int; email: str; password_hash: str; is_admin: bool

class UserPublic(BaseModel):          # the API contract
    id: int; email: str

@app.get("/users/{id}", response_model=UserPublic)
def get_user(id: int):
    return db_user                    # extra fields are dropped and the output is validated

@app.get("/users/{id}")
def get_user(id: int) -> UserPublic:  # same effect via the return annotation
```
- If you return an object of a *different* class than the annotation, use `response_model=` (type checkers would complain about the annotation).
- Response models also generate the **response schema** in OpenAPI, which is what frontend codegen reads.
- `response_model_exclude_none=True` drops `null` fields.

### Status codes and headers
```python
from fastapi import Response, status

@app.post("/users", status_code=status.HTTP_201_CREATED)
def create(user: UserCreate, response: Response):
    response.headers["Location"] = f"/users/{new.id}"
    return new

@app.delete("/users/{id}", status_code=204)   # 204 = no body
def delete(id: int) -> None: ...
```
| Code | Use |
|---|---|
| 200 | OK (GET, PUT/PATCH returning the resource) |
| 201 | Created (POST), plus a `Location` header |
| 202 | Accepted (async job queued) |
| 204 | No Content (DELETE, or a PUT that returns nothing) |
| 400 / 422 | bad request / validation failed |
| 401 / 403 | not authenticated / authenticated but not allowed |
| 404 / 409 | missing / conflict (duplicate, version mismatch) |
| 429 | rate limited |

### Computed fields and generic envelopes
```python
from pydantic import computed_field
from typing import Generic, TypeVar
T = TypeVar("T")

class UserPublic(BaseModel):
    first_name: str; last_name: str
    @computed_field
    @property
    def display_name(self) -> str: return f"{self.first_name} {self.last_name}"

class Page(BaseModel, Generic[T]):            # Page[UserPublic] shows up in OpenAPI
    items: list[T]; total: int; limit: int; offset: int
```

## 🏋️ Exercise
`exercise/main.py` leaks `password_hash` and `internal_notes`, returns 200 everywhere, and has no envelope.
1. Create `UserPublic` (id, email, first_name, last_name, plus computed `display_name`) and use it for responses.
2. `POST /users` → **201** with a `Location: /users/{id}` header. It must not echo the password back.
3. `GET /users` → `Page[UserPublic]` with `limit` and `offset` query params.
4. `DELETE /users/{id}` → **204** with an empty body, or 404.

```bash
python check.py f04
```

## 💼 Interview angle
- *"How do you stop sensitive fields from leaking?"*: separate input, DB and output models, with `response_model` as an allow-list. Never `return user.__dict__`.
- *"201 vs 200 vs 204?"*: created (with `Location`) vs OK with a body vs success with no body.
- *"401 vs 403?"*: 401 means "who are you?" (missing or bad credentials). 403 means "I know who you are, and you can't do this."
- *"How do you design list responses?"*: an envelope (`items`, `total`, and either `limit/offset` or `next_cursor`) so you can add metadata without breaking clients. Top-level arrays can't be extended.
- *"How does the frontend stay in sync with the backend's types?"*: response models produce the OpenAPI spec, which feeds generated TS types and CI contract checks.
