import hashlib  # noqa: F401
import json  # noqa: F401
import time
from collections import defaultdict
from typing import Annotated  # noqa: F401

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response  # noqa: F401
from fastapi.routing import APIRoute  # noqa: F401
from pydantic import BaseModel, Field

PRODUCTS = {1: {"id": 1, "name": "Keyboard", "price_cents": 12999}, 2: {"id": 2, "name": "Mouse", "price_cents": 4999}}
ORDERS: dict[int, dict] = {}
IDEMPOTENCY: dict[str, tuple[str, int, dict]] = {}  # key -> (request fingerprint, status, body)
RATE_LIMIT, RATE_WINDOW = 5, 60
HITS: dict[str, list[float]] = defaultdict(list)


def get_now() -> float:
    """Clock dependency (tests override it)."""
    return time.time()


class ProductIn(BaseModel):
    name: str = Field(min_length=1)
    price_cents: int = Field(ge=0)


class OrderIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


def etag_for(data: dict) -> str:
    """TODO: a quoted strong ETag from a hash of the JSON (sort_keys=True), e.g. '"3f2a9c..."'."""
    raise NotImplementedError


v1 = APIRouter(prefix="/v1", tags=["v1"])


@v1.get("/products/{product_id}")
def get_product(product_id: int):
    """TODO:
    - 404 if missing
    - set ETag; if the request's If-None-Match equals it -> 304 with empty body
    - mark v1 deprecated: headers Deprecation: true and Link: </v2/products/{id}>; rel="successor-version"
    """
    return PRODUCTS[product_id]


@v1.put("/products/{product_id}")
def replace_product(product_id: int, data: ProductIn):
    """TODO optimistic concurrency: If-Match missing -> 428; stale -> 412; success -> 200 + new ETag."""
    PRODUCTS[product_id] = {"id": product_id, **data.model_dump()}
    return PRODUCTS[product_id]


@v1.post("/orders", status_code=201)
def create_order(data: OrderIn):
    """TODO idempotency:
    - Idempotency-Key header required (400)
    - same key + same body -> replay the stored response (same status/body) + header Idempotent-Replayed: true
    - same key + different body -> 422
    - unknown product -> 404
    """
    order_id = len(ORDERS) + 1
    ORDERS[order_id] = {"id": order_id, **data.model_dump()}
    return ORDERS[order_id]


@v1.get("/search")
def search(q: str = ""):
    """TODO rate limit via a dependency: RATE_LIMIT requests per RATE_WINDOW seconds per client
    (X-Client-Id header, else client IP), time from get_now(). Over the limit -> 429 with Retry-After.
    Successful responses carry X-RateLimit-Limit and X-RateLimit-Remaining."""
    return [p for p in PRODUCTS.values() if q.lower() in p["name"].lower()]


# TODO: v2 router: GET /v2/products/{id} -> {"id", "name", "price": {"amount": "129.99", "currency": "USD"}}

# TODO: generate_unique_id_function so operationIds are "<first tag>_<function name>", e.g. "v1_get_product"
app = FastAPI(title="F15 · REST design")
app.include_router(v1)
