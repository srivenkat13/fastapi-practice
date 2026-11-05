"""App assembly only: create the app and plug in routers. No endpoint logic lives here."""
from fastapi import FastAPI

from .config import get_settings
from .routers import authors, books, meta

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    for module in (books, authors, meta):
        app.include_router(module.router, prefix=API_PREFIX)
    return app


app = create_app()
