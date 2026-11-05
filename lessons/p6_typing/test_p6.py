import typing
from typing import Annotated

import pytest

from support import target

m = target(__file__)


def test_first_is_generic():
    assert m.first([3, 2]) == 3
    assert m.first([]) is None
    hints = typing.get_type_hints(m.first)
    assert hints.get("items") == list[m.T], "annotate items as list[T]"


def test_typed_dict():
    assert m.UserDict.__required_keys__ == {"id", "name"}
    assert m.UserDict.__optional_keys__ == {"email"}


def test_protocol_is_structural():
    class File:
        closed = False

        def close(self):
            self.closed = True

    f1, f2 = File(), File()
    assert isinstance(f1, m.Closeable)
    assert not isinstance("text", m.Closeable)
    assert m.close_all([f1, "x", 42, f2]) == 2
    assert f1.closed and f2.closed


# --- the toy FastAPI --------------------------------------------------------


def search(q: str, limit: Annotated[int, m.Range(1, 100)] = 20, in_stock: bool = False, min_price: float | None = None):
    return {"q": q, "limit": limit, "in_stock": in_stock, "min_price": min_price}


def test_converts_and_applies_defaults():
    assert m.call_with_query(search, {"q": "kb"}) == {"q": "kb", "limit": 20, "in_stock": False, "min_price": None}
    assert m.call_with_query(search, {"q": "kb", "limit": "5", "in_stock": "yes", "min_price": "9.5", "junk": "x"}) == {
        "q": "kb",
        "limit": 5,
        "in_stock": True,
        "min_price": 9.5,
    }


def test_optional_without_default_becomes_none():
    def f(tag: str | None):
        return tag

    assert m.call_with_query(f, {}) is None


def test_collects_all_errors():
    with pytest.raises(m.ValidationFailed) as info:
        m.call_with_query(search, {"limit": "500", "in_stock": "maybe", "min_price": "cheap"})
    errors = sorted(info.value.errors, key=lambda e: e["field"])
    assert errors == [
        {"field": "in_stock", "error": "invalid"},
        {"field": "limit", "error": "out_of_range"},
        {"field": "min_price", "error": "invalid"},
        {"field": "q", "error": "missing"},
    ]
