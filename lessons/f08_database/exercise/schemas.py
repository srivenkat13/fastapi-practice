from pydantic import BaseModel, ConfigDict, Field


class AuthorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # read attributes from ORM objects

    id: int
    name: str


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    isbn: str = Field(pattern=r"^\d{13}$")
    year: int = Field(ge=1450, le=2100)
    author_id: int


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    isbn: str
    year: int
    author: AuthorOut
