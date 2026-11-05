import base64
import binascii
import json
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from .data import ARTICLES

app = FastAPI(title="D2 · Search + cursor pagination")


def encode_cursor(article: dict) -> str:
    raw = json.dumps({"p": article["published_at"].isoformat(), "id": article["id"]})
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")  # opaque to clients


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        return datetime.fromisoformat(data["p"]), int(data["id"])
    except (binascii.Error, ValueError, KeyError, TypeError):
        raise HTTPException(400, "Invalid cursor")


def sort_key(a: dict) -> tuple:
    return (a["published_at"], a["id"])


@app.get("/articles")
def search_articles(
    q: Annotated[str | None, Query(min_length=1)] = None,
    tag: str | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    cursor: str | None = None,
):
    results = ARTICLES
    if q:
        results = [a for a in results if q.lower() in a["title"].lower()]
    if tag:
        results = [a for a in results if tag in a["tags"]]
    # Newest first; id breaks ties so the order is TOTAL (no duplicates or skips across pages).
    results = sorted(results, key=sort_key, reverse=True)
    if cursor:
        position = decode_cursor(cursor)
        # Keyset condition: strictly "after" the last item seen → (published_at, id) < cursor.
        # SQL: WHERE (published_at, id) < (:p, :id) ORDER BY published_at DESC, id DESC LIMIT :n  (index-friendly)
        results = [a for a in results if sort_key(a) < position]
    page = results[: limit + 1]  # fetch one extra to know if there's a next page
    has_more = len(page) > limit
    page = page[:limit]
    return {
        "items": [{**a, "published_at": a["published_at"].isoformat()} for a in page],
        "next_cursor": encode_cursor(page[-1]) if has_more else None,
    }
