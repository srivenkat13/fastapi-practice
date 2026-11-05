import base64  # noqa: F401
import binascii  # noqa: F401
import json  # noqa: F401
from datetime import datetime  # noqa: F401
from typing import Annotated  # noqa: F401

from fastapi import FastAPI, HTTPException, Query  # noqa: F401

from .data import ARTICLES

app = FastAPI(title="D2 · Search + cursor pagination")


@app.get("/articles")
def search_articles(page: int = 1):
    """⏱ 30 minutes. Replace page-number pagination with CURSOR (keyset) pagination.

    GET /articles?q=&tag=&limit=&cursor=
      q       case-insensitive title contains (min length 1)
      tag     article must have this tag
      limit   1..50, default 10
      cursor  opaque string from the previous response; malformed -> 400
    Order: newest first (published_at DESC), ties broken by id DESC.
    Response: {"items": [... published_at as ISO string ...], "next_cursor": str | None}
      next_cursor is None on the last page.
    Pages must stay correct even if NEW articles are inserted at the top between requests.
    """
    per_page = 10
    items = sorted(ARTICLES, key=lambda a: a["published_at"], reverse=True)
    chunk = items[(page - 1) * per_page : page * per_page]
    return {"items": [{**a, "published_at": a["published_at"].isoformat()} for a in chunk], "page": page}
