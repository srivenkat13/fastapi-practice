from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel

from . import db
from .cache import InMemoryCache, get_or_load  # noqa: F401

app = FastAPI(title="R2 · Caching")
PRODUCT_TTL = 60
NOT_FOUND_TTL = 10


def get_cache() -> InMemoryCache:
    """TODO: return ONE module-level InMemoryCache (tests override this dependency)."""
    raise NotImplementedError


Cache = Annotated[InMemoryCache, Depends(get_cache)]


class ProductIn(BaseModel):
    name: str
    price_cents: int


@app.get("/products/{product_id}")
async def get_product(product_id: int, response: Response):
    """TODO: cache-aside via get_or_load with key "product:<id>" and PRODUCT_TTL.
    Header X-Cache: HIT or MISS. Missing products: cache None for NOT_FOUND_TTL and return 404."""
    product = await db.get_product(product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    return product


@app.put("/products/{product_id}")
async def update_product(product_id: int, data: ProductIn):
    """TODO: after writing to the DB, invalidate the cached product."""
    return await db.update_product(product_id, data.model_dump())


@app.get("/catalog")
async def catalog():
    """TODO: Cache-Control: public, max-age=60, stale-while-revalidate=30"""
    return await db.list_products()


@app.get("/me/cart")
async def my_cart():
    """TODO: Cache-Control: private, no-store"""
    return {"items": []}
