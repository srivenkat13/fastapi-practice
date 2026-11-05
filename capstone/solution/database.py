from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./capstone_tasks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _sqlite_foreign_keys(dbapi_connection, _record):
    dbapi_connection.execute("PRAGMA foreign_keys=ON")  # SQLite ignores FKs unless asked


class Base(DeclarativeBase):
    pass


def get_session():
    with SessionLocal() as session:
        yield session
