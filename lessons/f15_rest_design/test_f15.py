import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset():
    main.PRODUCTS.clear()
    main.PRODUCTS.update({1: {"id": 1, "name": "Keyboard", "price_cents": 12999}, 2: {"id": 2, "name": "Mouse", "price_cents": 4999}})
    main.ORDERS.clear()
    main.IDEMPOTENCY.clear()
    main.HITS.clear()
    main.app.dependency_overrides.clear()


def test_versioning_and_deprecation():
    v1 = client.get("/v1/products/1")
    assert v1.json() == {"id": 1, "name": "Keyboard", "price_cents": 12999}
    assert v1.headers["deprecation"] == "true"
    assert v1.headers["link"] == '</v2/products/1>; rel="successor-version"'
    assert client.get("/v2/products/1").json() == {"id": 1, "name": "Keyboard", "price": {"amount": "129.99", "currency": "USD"}}
    assert client.get("/v2/products/9").status_code == 404


def test_etag_conditional_get():
    r = client.get("/v1/products/1")
    etag = r.headers["etag"]
    assert etag.startswith('"') and etag.endswith('"') and len(etag) > 4
    assert client.get("/v1/products/2").headers["etag"] != etag
    cached = client.get("/v1/products/1", headers={"If-None-Match": etag})
    assert cached.status_code == 304 and cached.content == b""
    assert client.get("/v1/products/1", headers={"If-None-Match": '"stale"'}).status_code == 200
    assert client.get("/v1/products/9").status_code == 404


def test_optimistic_concurrency():
    etag = client.get("/v1/products/1").headers["etag"]
    body = {"name": "Keyboard Pro", "price_cents": 14999}
    assert client.put("/v1/products/1", json=body).status_code == 428
    ok = client.put("/v1/products/1", json=body, headers={"If-Match": etag})
    assert ok.status_code == 200 and ok.headers["etag"] != etag
    # a second writer still holding the old ETag must not overwrite the change
    assert client.put("/v1/products/1", json={"name": "Lost update", "price_cents": 1}, headers={"If-Match": etag}).status_code == 412
    assert client.get("/v1/products/1").json()["name"] == "Keyboard Pro"


def test_idempotent_orders():
    order = {"product_id": 1, "quantity": 2}
    assert client.post("/v1/orders", json=order).status_code == 400
    first = client.post("/v1/orders", json=order, headers={"Idempotency-Key": "k1"})
    assert first.status_code == 201 and first.json()["id"] == 1
    retry = client.post("/v1/orders", json=order, headers={"Idempotency-Key": "k1"})
    assert retry.status_code == 201 and retry.json() == first.json()
    assert retry.headers["idempotent-replayed"] == "true"
    assert len(main.ORDERS) == 1, "a retried request must not create a second order"
    assert client.post("/v1/orders", json={"product_id": 2, "quantity": 1}, headers={"Idempotency-Key": "k1"}).status_code == 422
    assert client.post("/v1/orders", json={"product_id": 9, "quantity": 1}, headers={"Idempotency-Key": "k2"}).status_code == 404
    assert client.post("/v1/orders", json=order, headers={"Idempotency-Key": "k3"}).json()["id"] == 2


def test_rate_limit():
    now = [1000.0]
    main.app.dependency_overrides[main.get_now] = lambda: now[0]
    ada = {"X-Client-Id": "ada"}
    for i in range(5):
        r = client.get("/v1/search", params={"q": "key"}, headers=ada)
        assert r.status_code == 200 and r.headers["x-ratelimit-remaining"] == str(4 - i)
    assert r.headers["x-ratelimit-limit"] == "5"
    blocked = client.get("/v1/search", headers=ada)
    assert blocked.status_code == 429 and 0 < int(blocked.headers["retry-after"]) <= 60
    assert client.get("/v1/search", headers={"X-Client-Id": "bob"}).status_code == 200, "limits are per client"
    now[0] += 61
    assert client.get("/v1/search", headers=ada).status_code == 200, "window should reset"


def test_operation_ids():
    spec = client.get("/openapi.json").json()
    ids = {op["operationId"] for path in spec["paths"].values() for op in path.values()}
    assert {"v1_get_product", "v1_replace_product", "v1_create_order", "v1_search", "v2_get_product_v2"} <= ids
