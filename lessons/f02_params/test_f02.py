from fastapi.testclient import TestClient

from support import target

main = target(__file__, "main")
client = TestClient(main.app)


def ids(response):
    assert response.status_code == 200, response.text
    return [b["id"] for b in response.json()]


def test_get_book():
    assert client.get("/books/2").json()["title"] == "Dune"


def test_get_book_validation_and_404():
    assert client.get("/books/abc").status_code == 422
    assert client.get("/books/0").status_code == 422
    r = client.get("/books/999")
    assert r.status_code == 404 and r.json() == {"detail": "Book not found"}


def test_featured_route_order():
    assert ids(client.get("/books/featured")) == [1, 4]


def test_list_defaults():
    assert ids(client.get("/books")) == [1, 2, 3, 4, 5]


def test_filters():
    assert ids(client.get("/books", params={"q": "PYTHON"})) == [1, 3]
    assert ids(client.get("/books", params={"genre": "fiction"})) == [2, 5]
    assert ids(client.get("/books", params={"min_year": 2016})) == [1, 3]
    assert ids(client.get("/books?tag=classic&tag=scifi")) == [2, 5]
    assert ids(client.get("/books?tag=python&tag=beginner")) == [3]
    assert ids(client.get("/books", params={"genre": "tech", "min_year": 2020})) == [1]


def test_pagination():
    assert ids(client.get("/books", params={"offset": 1, "limit": 2})) == [2, 3]


def test_query_validation():
    assert client.get("/books", params={"genre": "poetry"}).status_code == 422
    assert client.get("/books", params={"limit": 0}).status_code == 422
    assert client.get("/books", params={"limit": 51}).status_code == 422
    assert client.get("/books", params={"min_year": 1000}).status_code == 422
    assert client.get("/books", params={"offset": -1}).status_code == 422


def test_genre_count():
    assert client.get("/genres/fiction/count").json() == {"genre": "fiction", "count": 2}
    assert client.get("/genres/poetry/count").status_code == 422


def test_limit_is_documented():
    params = client.get("/openapi.json").json()["paths"]["/books"]["get"]["parameters"]
    limit = next(p for p in params if p["name"] == "limit")
    assert limit["schema"]["maximum"] == 50
