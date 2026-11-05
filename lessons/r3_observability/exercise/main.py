import logging
import time  # noqa: F401
import uuid  # noqa: F401
from typing import Annotated, Callable  # noqa: F401

from fastapi import Depends, FastAPI, HTTPException, Request  # noqa: F401
from fastapi.responses import JSONResponse  # noqa: F401

from .observability import configure_logging, request_id_var  # noqa: F401

configure_logging()
access_log = logging.getLogger("app.access")
log = logging.getLogger("app.orders")
app = FastAPI(title="R3 · Observability")

# TODO 1: middleware
#   - request id from X-Request-ID or uuid4().hex; request_id_var.set(...) (and .reset(token) at the end!)
#   - add X-Request-ID to the response
#   - ALWAYS log one access line: access_log.info("request", extra={"method", "path", "status", "duration_ms"})
#
# TODO 2: in that same middleware, catch exceptions from call_next: log.exception("unhandled error", ...)
#   and return JSONResponse({"error": "internal_error", "request_id": <id>}, status_code=500) (+ X-Request-ID).
#   Why not @app.exception_handler(Exception)? It runs in Starlette's OUTERMOST middleware, after yours has
#   already reset the request-id context.


def check_db() -> bool:
    return True


def check_cache() -> bool:
    return True


def get_checks() -> dict[str, Callable[[], bool]]:
    return {"db": check_db, "cache": check_cache}


# TODO 3: GET /health -> {"status": "ok"}  (liveness: no dependency checks)
# TODO 4: GET /ready  -> run every check from Depends(get_checks) (a check that raises counts as "fail");
#   200 {"status": "ok", "checks": {"db": "ok", ...}} or 503 {"status": "unavailable", "checks": {...}}


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id == 13:
        raise RuntimeError("corrupted order row")
    if order_id > 100:
        raise HTTPException(404, "Order not found")
    print(f"order viewed {order_id}")  # 🐛 TODO: log.info("order viewed", extra={"order_id": order_id})
    return {"id": order_id, "status": "shipped"}
