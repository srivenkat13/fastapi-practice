"""The Cart API under test. Read the SPEC in the README, and write your tests against the spec, not this code.

`create_app(bugs=...)` exists so the grader can build *mutants*: copies of this app with one
realistic bug each. A good test suite fails on every mutant. (Peeking at the bug names won't help you
much; testing the spec carefully will.)
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

CATALOG = {"KB": 2500, "MOUSE": 1500, "CABLE": 300}  # unit prices in cents
MAX_QTY = 10


@dataclass(frozen=True)
class Coupon:
    code: str
    percent_off: int = 0
    amount_off_cents: int = 0
    min_subtotal_cents: int = 0
    expires_at: datetime | None = None


COUPONS = {
    "SAVE10": Coupon("SAVE10", percent_off=10, min_subtotal_cents=5000, expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc)),
    "FLAT500": Coupon("FLAT500", amount_off_cents=500),
    "OLD20": Coupon("OLD20", percent_off=20, expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc)),
}


def get_now() -> datetime:
    """The clock is a dependency so tests can control time: app.dependency_overrides[get_now] = lambda: ..."""
    return datetime.now(timezone.utc)


class AddItem(BaseModel):
    sku: str
    qty: int = Field(ge=1, le=MAX_QTY)


class ApplyCoupon(BaseModel):
    code: str


def create_app(bugs: frozenset[str] = frozenset()) -> FastAPI:
    app = FastAPI(title="F11 · Cart API")
    carts: dict[str, dict] = {}

    def current_user(x_user: Annotated[str | None, Header()] = None) -> str:
        if not x_user:
            raise HTTPException(401, "Missing X-User header")
        return x_user

    def optional_user(x_user: Annotated[str | None, Header()] = None) -> str:
        return x_user or "anonymous"

    User = Annotated[str, Depends(current_user)]
    Now = Annotated[datetime, Depends(get_now)]

    def cart_for(user: str) -> dict:
        key = "shared" if "shared_cart" in bugs else user
        return carts.setdefault(key, {"items": {}, "coupon": None})

    def coupon_error(coupon: Coupon, subtotal: int, now: datetime) -> str | None:
        if coupon.expires_at and now >= coupon.expires_at and "ignores_expiry" not in bugs:
            return "Coupon has expired"
        meets_min = subtotal > coupon.min_subtotal_cents if "min_order_exclusive" in bugs else subtotal >= coupon.min_subtotal_cents
        if not meets_min:
            return f"Order must be at least {coupon.min_subtotal_cents} cents"
        return None

    def summary(cart: dict, now: datetime) -> dict:
        items = [
            {"sku": sku, "qty": qty, "unit_price_cents": CATALOG[sku], "line_total_cents": CATALOG[sku] * qty}
            for sku, qty in sorted(cart["items"].items())
        ]
        subtotal = sum(i["line_total_cents"] for i in items)
        discount = 0
        coupon = COUPONS.get(cart["coupon"]) if cart["coupon"] else None
        if coupon and coupon_error(coupon, subtotal, now) is None:  # re-checked: the cart may have changed
            discount = subtotal * coupon.percent_off // 100 + coupon.amount_off_cents
            if "flat_negative" not in bugs:
                discount = min(discount, subtotal)
        else:
            coupon = None
        return {
            "items": items,
            "subtotal_cents": subtotal,
            "discount_cents": discount,
            "total_cents": subtotal - discount,
            "coupon": coupon.code if coupon else None,
        }

    @app.get("/cart")
    def get_cart(user: User, now: Now):
        return summary(cart_for(user), now)

    @app.post("/cart/items", status_code=201)
    def add_item(data: AddItem, user: User, now: Now):
        if data.sku not in CATALOG:
            raise HTTPException(404, "Unknown SKU")
        cart = cart_for(user)
        current = 0 if "qty_replaces" in bugs else cart["items"].get(data.sku, 0)
        if current + data.qty > MAX_QTY:
            raise HTTPException(409, f"At most {MAX_QTY} of one item")
        cart["items"][data.sku] = current + data.qty
        return summary(cart, now)

    delete_user = optional_user if "no_auth_on_delete" in bugs else current_user

    @app.delete("/cart/items/{sku}", status_code=204)
    def remove_item(sku: str, user: Annotated[str, Depends(delete_user)]) -> Response:
        cart = cart_for(user)
        if sku not in cart["items"]:
            raise HTTPException(404, "Item not in cart")
        del cart["items"][sku]
        return Response(status_code=204)

    @app.post("/cart/coupon")
    def apply_coupon(data: ApplyCoupon, user: User, now: Now):
        coupon = COUPONS.get(data.code.upper())
        if coupon is None:
            raise HTTPException(404, "Unknown coupon")
        cart = cart_for(user)
        subtotal = summary(cart, now)["subtotal_cents"]
        error = coupon_error(coupon, subtotal, now)
        if error:
            raise HTTPException(422, error)
        cart["coupon"] = coupon.code
        return summary(cart, now)

    return app


app = create_app()  # for `python run.py f11`
