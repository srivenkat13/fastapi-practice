# FastAPI vs Flask vs Django (vs Express/Nest)

## Short answer (for "which would you choose?")
> "For an API-first service I'd pick **FastAPI**: type hints drive validation, serialization and OpenAPI docs, it's async-native for I/O-heavy workloads, and dependency injection keeps auth and DB handling testable. I'd pick **Django** when the product needs an admin, auth, ORM and migrations out of the box, such as a CRUD-heavy internal tool or a content site. I'd keep **Flask** for existing codebases or small server-rendered apps. It's minimal and flexible, but you assemble validation, docs and structure yourself."

## Comparison
| | FastAPI | Flask | Django (+ DRF) |
|---|---|---|---|
| Released | 2018 | 2010 | 2005 |
| Style | micro, API-first | micro, unopinionated | batteries-included, opinionated |
| Protocol | ASGI | WSGI | WSGI + ASGI |
| Async | native | partial (async views still occupy a worker) | partial (async views; ORM mostly sync, async API improving) |
| Validation | Pydantic (from type hints) | add-on (marshmallow, pydantic) | forms / DRF serializers |
| API docs | automatic OpenAPI | add-on | add-on (drf-spectacular) |
| ORM | bring your own (SQLAlchemy, SQLModel) | bring your own (Flask-SQLAlchemy) | built-in Django ORM + migrations |
| Admin UI | no | Flask-Admin | ✅ built-in, excellent |
| Auth | build/compose (security utils + libs) | Flask-Login etc. | ✅ built-in users, sessions, permissions |
| DI | ✅ `Depends` | none (context globals) | none (middleware, mixins) |
| Templates | possible (Jinja) | ✅ Jinja | ✅ Django templates |
| Performance (I/O-bound) | high | moderate | moderate |
| Learning curve | low–medium (types, async) | low | medium–high (lots of conventions) |
| Typical use | microservices, ML/AI serving, BFFs, internal APIs | small services, prototypes, legacy | SaaS products, CMS, e-commerce, admin-heavy apps |

## Node equivalents (to anchor your mental model)
| Python | Closest Node |
|---|---|
| FastAPI | Fastify/Express + zod + swagger, or **NestJS** (DI, decorators) |
| Flask | Express |
| Django | NestJS + Prisma + AdminJS, or Rails-like frameworks |

## Trade-offs worth mentioning
- FastAPI's freedom means **you** choose the project structure, ORM and migrations, and teams need conventions (F07).
- FastAPI's `async` only helps if your whole I/O path is async. Otherwise use `def` endpoints.
- Django's ORM and admin save weeks on CRUD products. Django Ninja gives FastAPI-style typed APIs on top of Django.
- Flask's ecosystem is huge but uneven in maintenance. Many tutorials are old.
- Hiring market: FastAPI dominates new Python API work, especially AI/ML backends. Django dominates established product companies.
