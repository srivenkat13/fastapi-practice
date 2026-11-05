# F08 · SQLAlchemy 2.0 + SQLite: models, sessions, relationships

> FastAPI has no ORM built in. **SQLAlchemy 2.0** is the standard (alternatives: SQLModel, which is SQLAlchemy plus Pydantic from FastAPI's author, Tortoise, or raw `asyncpg`). SQLite needs no install; switching `DATABASE_URL` to Postgres later is a one-line change.

## 🧠 Concepts

### The pieces
| Piece | Role | Node analogue |
|---|---|---|
| `engine` | connection pool + dialect | `new Pool()` / Prisma client |
| `Session` | unit of work: tracks objects, flushes INSERT/UPDATE, commits a transaction | a transaction-scoped client |
| `DeclarativeBase` model | table mapping | Prisma model / TypeORM entity |
| `select(...)` | query builder | Kysely/Drizzle |
| Pydantic `schemas` | API contract (separate from tables!) | DTOs |

### Models (2.0 typed style)
```python
class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    subtitle: Mapped[str | None]                      # Optional → nullable column
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="books")
```

### A session per request (a yield dependency)
```python
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
def get_session():
    with SessionLocal() as session:
        yield session
DB = Annotated[Session, Depends(get_session)]
```
`expire_on_commit=False` keeps loaded attributes usable after `commit()`, so you don't get surprise re-queries or `DetachedInstanceError` while serializing the response.

### CRUD in 2.0 style
```python
db.get(Book, 1)                                            # by primary key
db.scalars(select(Book).where(Book.year > 2000)).all()     # list
db.scalar(select(func.count()).select_from(Book))          # a single value
db.add(obj); db.commit(); db.refresh(obj)                  # insert
obj.title = "New"; db.commit()                             # update (change tracking)
db.delete(obj); db.commit()                                # delete
```
On `IntegrityError` (unique or FK violation) you must call `db.rollback()` before using the session again.

### ⚠️ The N+1 problem
```python
books = db.scalars(select(Book)).all()      # 1 query
for b in books: b.author.name               # +1 query PER book (lazy loading)
```
Fix it with eager loading: `select(Book).options(selectinload(Book.author))` (2 queries total) or `joinedload` (1 JOIN query, which suits many-to-one).

### Migrations with Alembic (instead of `create_all`)
`create_all` only creates missing tables. It never alters columns. Real projects use Alembic:
```bash
alembic init migrations                      # once; set target_metadata = Base.metadata in env.py
alembic revision --autogenerate -m "add books.subtitle"   # diff models vs DB → a migration file (REVIEW IT)
alembic upgrade head                         # apply (run in CI/CD before the new code starts)
alembic downgrade -1
```

## 🏋️ Exercise
1. `database.py`: make `get_session` always close the session.
2. `models.py`: add `Book.author_id` (FK, indexed), the `Book.author` / `Author.books` relationships, and make `isbn` unique.
3. `main.py`: `POST /books` (404 for an unknown author, 409 for a duplicate ISBN), `GET /books/{id}`, and `GET /authors/{id}/books` (ordered by year).
4. Fix the **N+1** in `GET /books`. The test counts the SELECTs.

```bash
python check.py f08          # python run.py f08 creates ./f08_bookshelf.db
```

## 💼 Interview angle
- *"What's the N+1 problem and how do you fix it?"*: one query for the list plus one per row for a relation. Fix it with eager loading (`selectinload`/`joinedload`), and spot it in logs (`echo=True`) or with query-count tests like the one here.
- *"Why separate Pydantic schemas from ORM models?"*: the API contract and the storage schema change for different reasons, and it avoids leaking columns or allowing mass assignment. (SQLModel merges them, which is convenient but couples the two.)
- *"How do you manage schema changes in production?"*: Alembic migrations, reviewed and run before deploy, kept backwards-compatible (expand → migrate → contract).
- *"Session lifecycle in a web app?"*: one session (transaction) per request, through a dependency, always closed. Never a global session shared between requests.
- *"selectinload vs joinedload?"*: selectin runs a second `WHERE id IN (...)` query, which is good for collections. Joined uses a single JOIN, which is good for many-to-one but duplicates rows for collections.
