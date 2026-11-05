from datetime import timedelta

from fastapi.testclient import TestClient

from support import target

data = target(__file__, "data")
main = target(__file__, "main")
client = TestClient(main.app)


def walk(params=None, insert_after_first_page=None):
    ids, cursor, pages = [], None, 0
    while True:
        p = dict(params or {})
        if cursor:
            p["cursor"] = cursor
        r = client.get("/articles", params=p)
        assert r.status_code == 200, r.text
        body = r.json()
        assert set(body) == {"items", "next_cursor"}
        ids += [a["id"] for a in body["items"]]
        pages += 1
        if pages == 1 and insert_after_first_page:
            insert_after_first_page()
        cursor = body["next_cursor"]
        if cursor is None:
            return ids, pages
        assert pages < 100, "pagination never ends"


def expected(items):
    return [a["id"] for a in sorted(items, key=lambda a: (a["published_at"], a["id"]), reverse=True)]


def test_full_walk_has_no_gaps_or_duplicates():
    ids, pages = walk({"limit": 7})
    assert ids == expected(data.ARTICLES) and pages == 8


def test_ties_are_broken_by_id():
    first = client.get("/articles", params={"limit": 3}).json()["items"]
    assert [a["id"] for a in first] == [50, 49, 48], "48 and 49 share a timestamp: higher id first"
    assert first[0]["published_at"].startswith("2025-01-02")


def test_filters_with_cursor():
    ids, _ = walk({"q": "fastapi", "tag": "react", "limit": 3})
    want = [a for a in data.ARTICLES if "fastapi" in a["title"].lower() and "react" in a["tags"]]
    assert ids == expected(want) and ids


def test_last_page_and_exact_multiple():
    ids, pages = walk({"limit": 10})
    assert len(ids) == 50 and pages == 5, "50 items / 10 per page = 5 pages, without an empty 6th page"


def test_stable_when_new_items_arrive():
    newest = max(a["published_at"] for a in data.ARTICLES)
    snapshot = list(data.ARTICLES)

    def insert():
        data.ARTICLES.append({"id": 999, "title": "Breaking", "author": "x", "published_at": newest + timedelta(days=1), "tags": []})

    try:
        ids, _ = walk({"limit": 10}, insert_after_first_page=insert)
        assert ids == expected(snapshot), "offset pagination would repeat an item here; keyset must not"
    finally:
        data.ARTICLES[:] = snapshot


def test_validation():
    assert client.get("/articles", params={"cursor": "%%%not-base64"}).status_code == 400
    assert client.get("/articles", params={"cursor": "eyJ4IjogMX0"}).status_code == 400  # valid base64, wrong shape
    assert client.get("/articles", params={"limit": 0}).status_code == 422
    assert client.get("/articles", params={"limit": 51}).status_code == 422
