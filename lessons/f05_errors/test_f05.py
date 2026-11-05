import pytest
from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
# raise_server_exceptions=False: see what a real client would get for a 500 instead of a test crash
client = TestClient(main.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_stock():
    main.STOCK.update({1: 3, 2: 0})


def error(response, status):
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}, f"expected only an 'error' envelope, got {body}"
    assert set(body["error"]) == {"code", "message", "details"}
    return body["error"]


def test_domain_exceptions_exist():
    assert issubclass(main.NotFound, main.AppError) and issubclass(main.OutOfStock, main.AppError)
    with pytest.raises(main.NotFound):
        main.get_book(99)
    with pytest.raises(main.OutOfStock):
        main.reserve(2, 1)


def test_success_unchanged():
    assert client.post("/books/1/reserve", params={"quantity": 2}).json() == {"book_id": 1, "reserved": 2, "remaining": 1}


def test_not_found():
    e = error(client.get("/books/99"), 404)
    assert e == {"code": "not_found", "message": "Book 99 not found", "details": []}


def test_out_of_stock():
    e = error(client.post("/books/2/reserve"), 409)
    assert e["code"] == "out_of_stock" and e["message"] == "Book 2 is out of stock"


def test_validation_error_shape():
    e = error(client.post("/books/abc/reserve", params={"quantity": 0}), 422)
    assert e["code"] == "validation_error"
    fields = {d["field"] for d in e["details"]}
    assert fields == {"path.book_id", "query.quantity"}
    assert all(d["message"] for d in e["details"])


def test_unknown_route_and_method():
    assert error(client.get("/nope"), 404)["code"] == "http_404"
    assert error(client.delete("/books/1"), 405)["code"] == "http_405"


def test_500_does_not_leak():
    r = client.get("/boom")
    e = error(r, 500)
    assert e == {"code": "internal_error", "message": "Something went wrong", "details": []}
    assert "hunter2" not in r.text
