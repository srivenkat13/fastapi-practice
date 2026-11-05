"""Async SQLAlchemy: same models and queries, but `await`ed. Driver: aiosqlite (asyncpg for Postgres)."""
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

engine = create_async_engine("sqlite+aiosqlite:///./f12_notes.db")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(500))


async def get_async_session():
    async with SessionLocal() as session:
        yield session


async def create_tables(eng=engine):
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # run sync DDL inside the async connection
