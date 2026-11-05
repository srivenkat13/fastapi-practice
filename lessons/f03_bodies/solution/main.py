from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

app = FastAPI(title="F03 · Bodies")

Tags = list[str]


def _normalise_tags(tags: Tags | None) -> Tags | None:
    if tags is None:
        return None
    return sorted({t.strip().lower() for t in tags if t.strip()})


class AuthorIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None


class BookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200, examples=["Fluent Python"])
    isbn: str = Field(pattern=r"^\d{13}$", examples=["9781492056355"])
    year: int = Field(ge=1450, le=2100)
    price: float = Field(gt=0)
    sale_price: float | None = Field(default=None, gt=0)
    tags: Tags = Field(default_factory=list, max_length=5)
    author: AuthorIn

    @field_validator("tags")
    @classmethod
    def normalise_tags(cls, tags: Tags) -> Tags:
        return _normalise_tags(tags)

    @model_validator(mode="after")
    def sale_below_price(self):
        if self.sale_price is not None and self.sale_price >= self.price:
            raise ValueError("sale_price must be lower than price")
        return self


class BookUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    price: float | None = Field(default=None, gt=0)
    sale_price: float | None = Field(default=None, gt=0)
    tags: Tags | None = Field(default=None, max_length=5)

    @field_validator("tags")
    @classmethod
    def normalise_tags(cls, tags: Tags | None) -> Tags | None:
        return _normalise_tags(tags)


BOOKS: dict[int, dict] = {}


@app.post("/books", status_code=201)
def create_book(book: BookCreate):
    book_id = len(BOOKS) + 1
    BOOKS[book_id] = {"id": book_id, **book.model_dump()}
    return BOOKS[book_id]


@app.patch("/books/{book_id}")
def update_book(book_id: int, patch: BookUpdate):
    if book_id not in BOOKS:
        raise HTTPException(404, "Book not found")
    merged = {**BOOKS[book_id], **patch.model_dump(exclude_unset=True)}
    if merged["sale_price"] is not None and merged["sale_price"] >= merged["price"]:
        raise HTTPException(422, "sale_price must be lower than price")
    BOOKS[book_id] = merged
    return merged
