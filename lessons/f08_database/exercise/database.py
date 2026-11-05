from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker  # noqa: F401

DATABASE_URL = "sqlite:///./f08_bookshelf.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session():
    # 🐛 TODO: sessions are never closed, so connections leak. Use a `with` block (or try/finally).
    session = SessionLocal()
    yield session
