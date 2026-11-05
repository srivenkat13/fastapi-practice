from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./f08_bookshelf.db"

# check_same_thread=False: FastAPI runs sync endpoints in a threadpool, so a connection
# may be used by a different thread than the one that created it (SQLite-specific flag).
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session():
    """One session per request, always closed."""
    with SessionLocal() as session:  # Session is a context manager: closes on exit
        yield session
