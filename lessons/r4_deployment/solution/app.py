from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .settings import Settings


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title="R4 · Deployment",
        version=settings.version,
        # Public API docs are a reconnaissance gift. Hide them in prod (or put them behind auth).
        docs_url=None if settings.is_prod else "/docs",
        redoc_url=None if settings.is_prod else "/redoc",
        openapi_url=None if settings.is_prod else "/openapi.json",
    )
    app.state.settings = settings

    if settings.is_prod:
        # Reject requests whose Host header isn't ours (host-header attacks, cache poisoning).
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if settings.is_prod:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/version")
    def version():
        return {"version": settings.version, "environment": settings.environment}

    return app
