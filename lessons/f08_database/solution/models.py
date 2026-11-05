from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    books: Mapped[list["Book"]] = relationship(back_populates="author", cascade="all, delete-orphan")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    year: Mapped[int]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), index=True)

    author: Mapped[Author] = relationship(back_populates="books")
