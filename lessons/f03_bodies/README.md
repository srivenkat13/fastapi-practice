# F03 · Request bodies with Pydantic v2

> A Pydantic model is a class whose type hints are **enforced at runtime**. Declare a model parameter and FastAPI reads the JSON body, validates it, converts it, and hands you a typed object. Invalid input gets a 422 with details. Think **zod schema + TS type in one**.

## 🧠 Concepts

```python
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, model_validator

class AuthorIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None

class BookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)   # reject unknown keys

    title: str = Field(min_length=1, max_length=200, examples=["Fluent Python"])
    isbn: str = Field(pattern=r"^\d{13}$")
    year: int = Field(ge=1450, le=2100)
    price: float = Field(gt=0)
    sale_price: float | None = None
    tags: list[str] = Field(default_factory=list, max_length=5)
    author: AuthorIn                                   # nested model = nested JSON object

    @field_validator("tags")                           # runs on one field
    @classmethod
    def normalise_tags(cls, tags: list[str]) -> list[str]:
        return sorted({t.strip().lower() for t in tags})

    @model_validator(mode="after")                     # runs on the whole object (cross-field rules)
    def check_sale(self):
        if self.sale_price is not None and self.sale_price >= self.price:
            raise ValueError("sale_price must be lower than price")
        return self

@app.post("/books", status_code=201)
def create_book(book: BookCreate):     # a model parameter is read from the body
    book.title                          # typed attribute access
    book.model_dump()                   # → dict  (v1: .dict())
```

### Pydantic v2 cheat sheet
| Task | v2 API |
|---|---|
| model → dict / JSON | `m.model_dump()`, `m.model_dump_json()` |
| dict → model (validate) | `Model.model_validate(data)` / `Model(**data)` |
| only fields the client sent | `m.model_dump(exclude_unset=True)` ← **PATCH** |
| copy with changes | `m.model_copy(update={...})` |
| ORM object → model | `model_config = ConfigDict(from_attributes=True)` (F08) |
| field constraints | `Field(gt=, ge=, min_length=, pattern=, max_length=)` |
| custom validation | `@field_validator`, `@model_validator`, or `Annotated[str, AfterValidator(fn)]` |
| JSON schema | `Model.model_json_schema()` |

Coercion: in the default "lax" mode `"5"` becomes `5` for an `int` field. Use `Field(strict=True)` or `ConfigDict(strict=True)` to refuse that.

### Body + path + query together
```python
@app.patch("/books/{book_id}")
def update(book_id: int, patch: BookUpdate, notify: bool = False): ...
```
FastAPI tells them apart: names in the path template are path params, Pydantic models are the body, and simple types are query params. Use `Body(embed=True)` for a single scalar in the body.

### PATCH: tell "not sent" apart from "set to null"
```python
class BookUpdate(BaseModel):            # every field optional
    title: str | None = None
    price: float | None = None

changes = patch.model_dump(exclude_unset=True)   # {"price": 10} if only price was sent
```

## 🏋️ Exercise
In `exercise/main.py`, finish `BookCreate` and `BookUpdate`, and implement `POST /books` (201, returns the stored book with an `id`) and `PATCH /books/{id}` (partial update, 404 if missing).

```bash
python check.py f03          # then try invalid payloads in /docs
```

## 💼 Interview angle
- *"How do you validate request bodies?"*: with Pydantic models. Field constraints cover simple rules, field and model validators cover the rest, and it's all reflected in OpenAPI automatically.
- *"PUT vs PATCH?"*: PUT replaces the whole resource (all fields required). PATCH updates partially, using `exclude_unset`.
- *"How do you reject unexpected fields?"*: `extra="forbid"`. That catches typos and mass-assignment attempts like `{"is_admin": true}`.
- *"Pydantic v1 → v2 differences?"*: Rust core (`pydantic-core`) that's 5–50× faster; `.dict()` became `.model_dump()`, `@validator` became `@field_validator`, `orm_mode` became `from_attributes`, and `Config` became `model_config`.
- *"Why validate at the edge?"*: so the core logic can trust its types. "Parse, don't validate."
