from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    author: Mapped[str] = mapped_column(String(100), index=True)
    genre: Mapped[str] = mapped_column(String(30), index=True)
    year: Mapped[int]
    price_cents: Mapped[int]
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
