from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel

from . import db
from .cache import InMemoryCache, get_or_load

app = FastAPI(title="R2 · Caching")
PRODUCT_TTL = 60
NOT_FOUND_TTL = 10
_cache = InMemoryCache()


def get_cache() -> InMemoryCache:
    return _cache


Cache = Annotated[InMemoryCache, Depends(get_cache)]


class ProductIn(BaseModel):
    name: str
    price_cents: int


def product_key(product_id: int) -> str:
    return f"product:{product_id}"  # namespaced keys; add a version prefix (v2:product:1) to bust everything on deploys


@app.get("/products/{product_id}")
async def get_product(product_id: int, cache: Cache, response: Response):
    product, hit = await get_or_load(cache, product_key(product_id), lambda: db.get_product(product_id), PRODUCT_TTL)
    response.headers["X-Cache"] = "HIT" if hit else "MISS"
    if product is None:
        if not hit:
            cache.set(product_key(product_id), None, NOT_FOUND_TTL)  # negative caching, with a SHORT ttl
        raise HTTPException(404, "Product not found", headers={"X-Cache": response.headers["X-Cache"]})
    return product


@app.put("/products/{product_id}")
async def update_product(product_id: int, data: ProductIn, cache: Cache):
    product = await db.update_product(product_id, data.model_dump())  # 1) write the source of truth
    cache.delete(product_key(product_id))  # 2) invalidate (delete, don't update: avoids racing writers)
    return product


@app.get("/catalog")
async def catalog(response: Response):
    # HTTP caching: browsers and CDNs keep it 60s, then may serve stale for 30s while revalidating.
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
    return await db.list_products()


@app.get("/me/cart")
async def my_cart(response: Response):
    response.headers["Cache-Control"] = "private, no-store"  # user-specific: never in a shared cache
    return {"items": []}
