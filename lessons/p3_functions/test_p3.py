import pytest

from support import target

m = target(__file__)


def test_build_query():
    assert m.build_query("/users") == "/users"
    assert m.build_query("/users", team="core", page=2) == "/users?page=2&team=core"
    assert m.build_query("/users", sort="-name", q=None) == "/users?sort=-name"


def test_build_query_sort_is_keyword_only():
    with pytest.raises(TypeError):
        m.build_query("/users", "-name")


def test_append_tag_has_no_shared_default():
    assert m.append_tag("a") == ["a"]
    assert m.append_tag("b") == ["b"]
    assert m.append_tag("c", ["x"]) == ["x", "c"]


def test_make_counter_closures_are_independent():
    a, b = m.make_counter(), m.make_counter(10)
    assert [a(), a(), b(), a()] == [1, 2, 11, 3]


def test_retry_succeeds_after_failures():
    calls = []

    @m.retry(times=3, exceptions=(ConnectionError,))
    def flaky():
        """docs"""
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("boom")
        return "ok"

    assert flaky() == "ok"
    assert len(calls) == 3
    assert flaky.__name__ == "flaky" and flaky.__doc__ == "docs"


def test_retry_reraises_and_ignores_other_errors():
    @m.retry(times=2, exceptions=(ConnectionError,))
    def always():
        raise ConnectionError("down")

    with pytest.raises(ConnectionError):
        always()

    calls = []

    @m.retry(times=5, exceptions=(ConnectionError,))
    def wrong_kind():
        calls.append(1)
        raise ValueError("not retryable")

    with pytest.raises(ValueError):
        wrong_kind()
    assert len(calls) == 1


def test_memoize():
    calls = []

    @m.memoize
    def square(x):
        calls.append(x)
        return x * x

    assert square(4) == 16 and square(4) == 16 and square(5) == 25
    assert calls == [4, 5]
    assert square.cache == {(4,): 16, (5,): 25}
    assert square.__name__ == "square"


def test_register_returns_function_unchanged():
    def handler():
        return "hi"

    result = m.register("/hello")(handler)
    assert result is handler
    assert m.ROUTES["/hello"] is handler
