from fastapi import FastAPI, Request  # noqa: F401
from fastapi.middleware.trustedhost import TrustedHostMiddleware  # noqa: F401

from .settings import Settings


def create_app(settings: Settings) -> FastAPI:
    """TODO:
    - disable /docs, /redoc and /openapi.json when settings.is_prod
    - in prod: TrustedHostMiddleware(allowed_hosts=settings.allowed_hosts)
    - always: X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: no-referrer
    - prod only: Strict-Transport-Security: max-age=63072000; includeSubDomains
    - GET /health -> {"status": "ok"};  GET /version -> {"version", "environment"}
    """
    app = FastAPI(title="R4 · Deployment")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
