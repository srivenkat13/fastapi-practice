"""Reference test suite for the Cart API: kills every mutant."""
from datetime import datetime, timezone

import pytest

from lessons.f11_testing.cartapp.app import get_now

ADA, BOB = {"X-User": "ada"}, {"X-User": "bob"}


def add(client, sku, qty, headers=ADA):
    return client.post("/cart/items", json={"sku": sku, "qty": qty}, headers=headers)


@pytest.fixture
def at(app):
    """Freeze the clock: at(2031, 1, 1)."""

    def freeze(*ymd):
        app.dependency_overrides[get_now] = lambda: datetime(*ymd, tzinfo=timezone.utc)

    return freeze


# --- auth ------------------------------------------------------------------------
@pytest.mark.parametrize(
    "method, path, body",
    [("get", "/cart", None), ("post", "/cart/items", {"sku": "KB", "qty": 1}),
     ("delete", "/cart/items/KB", None), ("post", "/cart/coupon", {"code": "FLAT500"})],
)
def test_every_endpoint_requires_user(client, method, path, body):
    assert client.request(method, path, json=body).status_code == 401


# --- items -----------------------------------------------------------------------
def test_add_item_and_totals(client):
    r = add(client, "KB", 2)
    assert r.status_code == 201
    body = r.json()
    assert body["items"] == [{"sku": "KB", "qty": 2, "unit_price_cents": 2500, "line_total_cents": 5000}]
    assert (body["subtotal_cents"], body["discount_cents"], body["total_cents"]) == (5000, 0, 5000)


def test_adding_same_sku_increments(client):
    add(client, "CABLE", 2)
    assert add(client, "CABLE", 3).json()["items"][0]["qty"] == 5


def test_quantity_limits(client):
    assert add(client, "KB", 0).status_code == 422
    assert add(client, "KB", 11).status_code == 422
    add(client, "KB", 6)
    assert add(client, "KB", 5).status_code == 409


def test_unknown_sku(client):
    assert add(client, "NOPE", 1).status_code == 404


def test_carts_are_per_user(client):
    add(client, "KB", 1, ADA)
    add(client, "MOUSE", 1, BOB)
    assert [i["sku"] for i in client.get("/cart", headers=ADA).json()["items"]] == ["KB"]
    assert [i["sku"] for i in client.get("/cart", headers=BOB).json()["items"]] == ["MOUSE"]


def test_remove_item(client):
    add(client, "KB", 1)
    assert client.delete("/cart/items/KB", headers=ADA).status_code == 204
    assert client.get("/cart", headers=ADA).json()["items"] == []
    assert client.delete("/cart/items/KB", headers=ADA).status_code == 404


# --- coupons ---------------------------------------------------------------------
def test_percent_coupon_minimum_is_inclusive(client, at):
    at(2025, 6, 1)
    add(client, "KB", 1)
    assert client.post("/cart/coupon", json={"code": "SAVE10"}, headers=ADA).status_code == 422  # 2500 < 5000
    add(client, "KB", 1)  # exactly 5000
    r = client.post("/cart/coupon", json={"code": "save10"}, headers=ADA)
    assert r.status_code == 200
    assert (r.json()["discount_cents"], r.json()["total_cents"], r.json()["coupon"]) == (500, 4500, "SAVE10")


def test_coupon_dropped_when_cart_falls_below_minimum(client, at):
    at(2025, 6, 1)
    add(client, "KB", 2)
    client.post("/cart/coupon", json={"code": "SAVE10"}, headers=ADA)
    add(client, "CABLE", 1)
    client.delete("/cart/items/KB", headers=ADA)
    body = client.get("/cart", headers=ADA).json()
    assert body["coupon"] is None and body["discount_cents"] == 0


@pytest.mark.parametrize("code, when", [("SAVE10", (2030, 1, 1)), ("SAVE10", (2031, 5, 5)), ("OLD20", (2025, 1, 1))])
def test_expired_coupons_rejected(client, at, code, when):
    at(*when)
    add(client, "KB", 4)
    r = client.post("/cart/coupon", json={"code": code}, headers=ADA)
    assert r.status_code == 422 and "expired" in r.json()["detail"].lower()


def test_flat_coupon_never_goes_negative(client):
    add(client, "CABLE", 1)  # 300 < 500
    body = client.post("/cart/coupon", json={"code": "FLAT500"}, headers=ADA).json()
    assert body["discount_cents"] == 300 and body["total_cents"] == 0


def test_unknown_coupon(client):
    assert client.post("/cart/coupon", json={"code": "FREE"}, headers=ADA).status_code == 404
