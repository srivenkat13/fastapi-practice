import logging
import time
import uuid
from typing import Annotated, Callable

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .observability import configure_logging, request_id_var

configure_logging()
access_log = logging.getLogger("app.access")
log = logging.getLogger("app.orders")
app = FastAPI(title="R3 · Observability")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    status = 500
    try:
        try:
            response = await call_next(request)
        except Exception:
            # Handle crashes HERE, while request_id_var is still set. (An @app.exception_handler(Exception)
            # runs in Starlette's outermost middleware, after this one has already reset the context.)
            log.exception("unhandled error", extra={"path": request.url.path})
            response = JSONResponse({"error": "internal_error", "request_id": request_id}, status_code=500)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        access_log.info(
            "request",
            extra={"method": request.method, "path": request.url.path, "status": status,
                   "duration_ms": round((time.perf_counter() - start) * 1000, 2)},
        )
        request_id_var.reset(token)


# ---- health checks ---------------------------------------------------------------------
def check_db() -> bool:
    return True  # real: SELECT 1 with a short timeout


def check_cache() -> bool:
    return True  # real: redis.ping()


def get_checks() -> dict[str, Callable[[], bool]]:
    return {"db": check_db, "cache": check_cache}


@app.get("/health")
def liveness():
    """Liveness: is the process alive? Never check dependencies here (a DB blip shouldn't restart every pod)."""
    return {"status": "ok"}


@app.get("/ready")
def readiness(checks: Annotated[dict[str, Callable[[], bool]], Depends(get_checks)]):
    """Readiness: can this instance serve traffic right now? A failure takes it out of the load balancer."""
    results = {}
    for name, check in checks.items():
        try:
            results[name] = "ok" if check() else "fail"
        except Exception:
            results[name] = "fail"
    healthy = all(v == "ok" for v in results.values())
    body = {"status": "ok" if healthy else "unavailable", "checks": results}
    return JSONResponse(body, status_code=200 if healthy else 503)


# ---- business endpoints ----------------------------------------------------------------------
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id == 13:
        raise RuntimeError("corrupted order row")
    if order_id > 100:
        raise HTTPException(404, "Order not found")
    log.info("order viewed", extra={"order_id": order_id})
    return {"id": order_id, "status": "shipped"}
