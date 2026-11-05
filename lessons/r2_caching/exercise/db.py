"""A slow fake database that counts its calls."""
import asyncio

PRODUCTS = {1: {"id": 1, "name": "Keyboard", "price_cents": 12999}, 2: {"id": 2, "name": "Mouse", "price_cents": 4999}}
CALLS = {"get_product": 0, "list_products": 0}


async def get_product(product_id: int) -> dict | None:
    CALLS["get_product"] += 1
    await asyncio.sleep(0.05)
    product = PRODUCTS.get(product_id)
    return dict(product) if product else None


async def list_products() -> list[dict]:
    CALLS["list_products"] += 1
    await asyncio.sleep(0.05)
    return [dict(p) for p in PRODUCTS.values()]


async def update_product(product_id: int, data: dict) -> dict:
    await asyncio.sleep(0.01)
    PRODUCTS[product_id] = {"id": product_id, **data}
    return dict(PRODUCTS[product_id])
