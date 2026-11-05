from sqlalchemy import ForeignKey, String  # noqa: F401
from sqlalchemy.orm import Mapped, mapped_column, relationship  # noqa: F401

from .database import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # TODO: books: Mapped[list["Book"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    isbn: Mapped[str] = mapped_column(String(13))  # TODO: unique=True
    year: Mapped[int]
    # TODO: author_id: foreign key to authors.id (indexed)
    # TODO: author: relationship(back_populates="books")
