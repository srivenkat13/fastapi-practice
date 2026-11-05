from datetime import date, datetime, timezone  # noqa: F401

from sqlalchemy import Column, ForeignKey, String, Table, Text  # noqa: F401
from sqlalchemy.orm import Mapped, mapped_column, relationship  # noqa: F401

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    # TODO: description (Text, default ""), owner_id (FK users.id), created_at (default utcnow)
    # TODO: relationships: owner, members (secondary=project_members), tasks (cascade delete)


# TODO: class Task(Base) with: id, project_id (FK projects.id, ondelete CASCADE), title, description,
#       status ("todo" default), priority ("medium" default), due_date (date | None),
#       assignee_id (FK users.id, ondelete SET NULL, nullable), created_by_id, created_at, completed_at,
#       and relationships to project (back_populates="tasks") and assignee.
