"""YOUR test suite for the Cart API (spec: ../README.md).

Use the fixtures from ../conftest.py:
    client   a TestClient for a fresh app
    app      that app, for app.dependency_overrides[get_now] = lambda: some_datetime

Run just your tests:   python -m pytest lessons/f11_testing/exercise/tests_cart_api.py -v
Grade (mutation testing): python check.py f11
"""
from datetime import datetime, timezone  # noqa: F401

import pytest  # noqa: F401

from lessons.f11_testing.cartapp.app import get_now  # noqa: F401

ADA = {"X-User": "ada"}


def test_cart_requires_user_header(client):
    assert client.get("/cart").status_code == 401


def test_add_item_returns_cart(client):
    r = client.post("/cart/items", json={"sku": "KB", "qty": 2}, headers=ADA)
    assert r.status_code == 201
    assert r.json()["subtotal_cents"] == 5000


# TODO: write tests until every mutant is caught. Ideas from the spec:
#   - each user has their own cart
#   - adding the same SKU twice increments the quantity
#   - coupon minimums are inclusive (exactly 5000 qualifies)
#   - expired coupons are rejected (control the clock with app.dependency_overrides[get_now])
#   - FLAT500 never makes the total negative
#   - every /cart endpoint requires X-User, including DELETE
