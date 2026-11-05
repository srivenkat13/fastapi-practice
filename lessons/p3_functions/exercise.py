"""P3 exercise."""
import functools  # noqa: F401  (you'll want functools.wraps)


def build_query(path: str, *, sort: str | None = None, **filters) -> str:
    """Build a URL from a path, an optional keyword-only `sort`, and any filters (skip None values).
    Filters are sorted by key so the output is deterministic.

    build_query("/users")                          -> "/users"
    build_query("/users", team="core", page=2)     -> "/users?page=2&team=core"
    build_query("/users", sort="-name", q=None)    -> "/users?sort=-name"
    """
    raise NotImplementedError


def append_tag(tag: str, tags: list[str] = []) -> list[str]:  # 🐛 fix me
    """Return the tags list with `tag` appended. Calling append_tag("a") twice must give ["a"] both times."""
    tags.append(tag)
    return tags


def make_counter(start: int = 0):
    """Return a function that returns start+1, start+2, ... on each call (a closure)."""
    raise NotImplementedError


def retry(times: int, exceptions: tuple = (Exception,)):
    """Decorator factory: call the function up to `times` times while it raises one of `exceptions`.
    Re-raise the last error if every attempt fails. Preserve the wrapped function's __name__.

    @retry(times=3, exceptions=(ConnectionError,))
    def fetch(): ...
    """
    raise NotImplementedError


def memoize(fn):
    """Decorator caching results by positional args. Expose the cache dict as `wrapper.cache`."""
    raise NotImplementedError


ROUTES: dict[str, object] = {}


def register(path: str):
    """A tiny `@app.get(path)`: store the function in ROUTES[path] and return the function UNCHANGED."""
    raise NotImplementedError
