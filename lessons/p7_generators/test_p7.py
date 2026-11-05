import inspect
from itertools import islice

import pytest

from support import target

m = target(__file__)


def test_countdown_iterator_class():
    assert list(m.Countdown(3)) == [3, 2, 1]
    assert list(m.Countdown(0)) == []


def test_countdown_generator():
    assert inspect.isgeneratorfunction(m.countdown)
    assert list(m.countdown(3)) == [3, 2, 1]


def make_api(total):
    calls = []

    def fetch_page(offset, limit):
        calls.append(offset)
        return list(range(total))[offset : offset + limit]

    return fetch_page, calls


def test_paginate_fetches_everything():
    fetch, calls = make_api(25)
    assert list(m.paginate(fetch, 10)) == list(range(25))
    assert calls == [0, 10, 20]


def test_paginate_exact_multiple_needs_one_empty_page():
    fetch, calls = make_api(20)
    assert len(list(m.paginate(fetch, 10))) == 20
    assert calls == [0, 10, 20]


def test_paginate_is_lazy():
    fetch, calls = make_api(1000)
    assert list(islice(m.paginate(fetch, 10), 3)) == [0, 1, 2]
    assert calls == [0]


def test_batched_works_on_generators():
    assert list(m.batched("abcde", 2)) == [("a", "b"), ("c", "d"), ("e",)]
    assert list(m.batched((x for x in range(4)), 2)) == [(0, 1), (2, 3)]


def test_error_codes():
    lines = ["2024-01-01 INFO 200 ok", "", "2024-01-01 ERROR 503 upstream timeout", "2024-01-02 ERROR 500 boom"]
    result = m.error_codes(lines)
    assert not isinstance(result, list), "return a lazy iterator, not a list"
    assert list(result) == [503, 500]


def test_managed_resource_normal_flow():
    log = []
    gen = m.managed_resource(log)
    assert next(gen) == "resource" and log == ["open"]
    with pytest.raises(StopIteration):
        next(gen)  # FastAPI resumes the generator after the response
    assert log == ["open", "close"]


def test_managed_resource_cleans_up_on_error():
    log = []
    gen = m.managed_resource(log)
    next(gen)
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("endpoint crashed"))  # FastAPI re-raises endpoint errors at the yield
    assert log == ["open", "close"]
