import asyncio

import httpx
import pytest

from support import target

main = target(__file__, "main")
pytestmark = pytest.mark.anyio
PAY = {"amount_cents": 5000, "currency": "USD", "customer_id": "cus_1"}


@pytest.fixture
async def client():
    for store in (main.PAYMENTS, main.GATEWAY_CALLS, main.IDEMPOTENCY, main.LOCKS):
        store.clear()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://t") as c:
        yield c


def key(k):
    return {"Idempotency-Key": k}


def charges():
    return [c for c in main.GATEWAY_CALLS if c["kind"] == "charge"]


async def test_key_required(client):
    assert (await client.post("/payments", json=PAY)).status_code == 400


async def test_retry_replays_without_recharging(client):
    first = await client.post("/payments", json=PAY, headers=key("k1"))
    retry = await client.post("/payments", json=PAY, headers=key("k1"))
    assert first.status_code == retry.status_code == 201
    assert retry.json() == first.json() and retry.headers["idempotent-replayed"] == "true"
    assert "idempotent-replayed" not in first.headers
    assert len(charges()) == 1
    other = await client.post("/payments", json=PAY, headers=key("k2"))
    assert other.json()["id"] == 2 and len(charges()) == 2


async def test_key_reuse_with_different_body(client):
    await client.post("/payments", json=PAY, headers=key("k1"))
    r = await client.post("/payments", json={**PAY, "amount_cents": 9999}, headers=key("k1"))
    assert r.status_code == 409 and len(charges()) == 1


async def test_concurrent_duplicates_charge_once(client):
    results = await asyncio.gather(*(client.post("/payments", json=PAY, headers=key("double-click")) for _ in range(5)))
    assert {r.status_code for r in results} == {201}
    assert len({r.json()["id"] for r in results}) == 1
    assert len(charges()) == 1, f"{len(charges())} charges for one double-clicked payment!"


async def test_validation_errors_are_not_cached(client):
    assert (await client.post("/payments", json={**PAY, "amount_cents": 0}, headers=key("k1"))).status_code == 422
    assert (await client.post("/payments", json=PAY, headers=key("k1"))).status_code == 201


async def test_refunds(client):
    pid = (await client.post("/payments", json=PAY, headers=key("p"))).json()["id"]
    r = await client.post(f"/payments/{pid}/refunds", json={"amount_cents": 2000}, headers=key("r1"))
    assert r.status_code == 201 and r.json()["payment_status"] == "partially_refunded"
    assert (await client.post(f"/payments/{pid}/refunds", json={"amount_cents": 3001}, headers=key("r2"))).status_code == 422
    assert (await client.post(f"/payments/{pid}/refunds", json={"amount_cents": 2000}, headers=key("r1"))).headers["idempotent-replayed"] == "true"
    r = await client.post(f"/payments/{pid}/refunds", json={"amount_cents": 3000}, headers=key("r3"))
    assert r.json()["payment_status"] == "refunded"
    payment = (await client.get(f"/payments/{pid}")).json()
    assert payment["refunded_cents"] == 5000 and payment["status"] == "refunded"
    assert (await client.post("/payments/99/refunds", json={"amount_cents": 1}, headers=key("r4"))).status_code == 404
    assert (await client.post(f"/payments/{pid}/refunds", json={"amount_cents": 1})).status_code == 400


async def test_concurrent_refunds_cannot_over_refund(client):
    pid = (await client.post("/payments", json=PAY, headers=key("p"))).json()["id"]
    results = await asyncio.gather(
        *(client.post(f"/payments/{pid}/refunds", json={"amount_cents": 3000}, headers=key(f"r{i}")) for i in range(3))
    )
    assert sorted(r.status_code for r in results) == [201, 422, 422]
    assert (await client.get(f"/payments/{pid}")).json()["refunded_cents"] == 3000


async def test_keys_are_scoped_per_endpoint(client):
    pid = (await client.post("/payments", json=PAY, headers=key("same"))).json()["id"]
    r = await client.post(f"/payments/{pid}/refunds", json={"amount_cents": 100}, headers=key("same"))
    assert r.status_code == 201 and "idempotent-replayed" not in r.headers
