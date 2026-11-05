import hashlib
import json
import math
import time
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field

PRODUCTS = {1: {"id": 1, "name": "Keyboard", "price_cents": 12999}, 2: {"id": 2, "name": "Mouse", "price_cents": 4999}}
ORDERS: dict[int, dict] = {}
IDEMPOTENCY: dict[str, tuple[str, int, dict]] = {}  # key -> (request fingerprint, status, body)
RATE_LIMIT, RATE_WINDOW = 5, 60
HITS: dict[str, list[float]] = defaultdict(list)


def get_now() -> float:
    return time.time()


class ErrorOut(BaseModel):
    detail: str


class ProductIn(BaseModel):
    name: str = Field(min_length=1)
    price_cents: int = Field(ge=0)


class OrderIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


def etag_for(data: dict) -> str:
    return '"' + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16] + '"'


def product_or_404(product_id: int) -> dict:
    if product_id not in PRODUCTS:
        raise HTTPException(404, "Product not found")
    return PRODUCTS[product_id]


# ---- rate limiting (fixed window log per client) -----------------------------------------
def rate_limit(request: Request, response: Response, now: Annotated[float, Depends(get_now)],
               x_client_id: Annotated[str | None, Header()] = None):
    client = x_client_id or (request.client.host if request.client else "unknown")
    hits = [t for t in HITS[client] if t > now - RATE_WINDOW]
    if len(hits) >= RATE_LIMIT:
        retry_after = max(1, math.ceil(hits[0] + RATE_WINDOW - now))
        raise HTTPException(429, "Too many requests", headers={"Retry-After": str(retry_after)})
    hits.append(now)
    HITS[client] = hits
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT - len(hits))


# ---- v1 ----------------------------------------------------------------------------------
v1 = APIRouter(prefix="/v1", tags=["v1"])


@v1.get("/products/{product_id}", responses={404: {"model": ErrorOut}, 304: {"description": "Not modified"}})
def get_product(product_id: int, response: Response, if_none_match: Annotated[str | None, Header()] = None):
    product = product_or_404(product_id)
    etag = etag_for(product)
    if if_none_match == etag:
        return Response(status_code=304, headers={"ETag": etag})  # client cache is still fresh: no body
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=0, must-revalidate"
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'</v2/products/{product_id}>; rel="successor-version"'
    return product


@v1.put("/products/{product_id}", responses={412: {"model": ErrorOut}, 428: {"model": ErrorOut}})
def replace_product(product_id: int, data: ProductIn, response: Response,
                    if_match: Annotated[str | None, Header()] = None):
    product = product_or_404(product_id)
    if if_match is None:
        raise HTTPException(428, "If-Match header required")  # 428 Precondition Required
    if if_match != etag_for(product):
        raise HTTPException(412, "Product was modified by someone else")  # lost-update prevention
    PRODUCTS[product_id] = {"id": product_id, **data.model_dump()}
    response.headers["ETag"] = etag_for(PRODUCTS[product_id])
    return PRODUCTS[product_id]


@v1.post("/orders", status_code=201)
def create_order(data: OrderIn, response: Response, idempotency_key: Annotated[str | None, Header()] = None):
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key header required")
    fingerprint = data.model_dump_json()
    if idempotency_key in IDEMPOTENCY:
        seen_fingerprint, status, body = IDEMPOTENCY[idempotency_key]
        if seen_fingerprint != fingerprint:
            raise HTTPException(422, "Idempotency-Key reused with a different request")
        response.status_code = status
        response.headers["Idempotent-Replayed"] = "true"
        return body
    product_or_404(data.product_id)
    order_id = len(ORDERS) + 1
    ORDERS[order_id] = {"id": order_id, **data.model_dump()}
    IDEMPOTENCY[idempotency_key] = (fingerprint, 201, ORDERS[order_id])
    return ORDERS[order_id]


@v1.get("/search", dependencies=[Depends(rate_limit)])
def search(q: str = ""):
    return [p for p in PRODUCTS.values() if q.lower() in p["name"].lower()]


# ---- v2: a breaking change (price becomes an object) lives side by side --------------------
v2 = APIRouter(prefix="/v2", tags=["v2"])


@v2.get("/products/{product_id}", responses={404: {"model": ErrorOut}})
def get_product_v2(product_id: int):
    p = product_or_404(product_id)
    return {"id": p["id"], "name": p["name"], "price": {"amount": f"{p['price_cents'] / 100:.2f}", "currency": "USD"}}


def operation_id(route: APIRoute) -> str:
    """Stable, readable operationIds → nice generated client method names (e.g. v1_get_product)."""
    return f"{route.tags[0]}_{route.name}"


app = FastAPI(title="F15 · REST design", generate_unique_id_function=operation_id)
app.include_router(v1)
app.include_router(v2)
