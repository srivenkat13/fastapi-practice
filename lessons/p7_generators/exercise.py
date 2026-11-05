"""P7 exercise."""
from typing import Callable, Iterable, Iterator


class Countdown:
    """Iterator protocol by hand: list(Countdown(3)) == [3, 2, 1]. Implement __iter__ and __next__."""

    def __init__(self, start: int):
        self.current = start


def countdown(n: int) -> Iterator[int]:
    """The same thing as a generator function: list(countdown(3)) == [3, 2, 1]."""
    raise NotImplementedError


def paginate(fetch_page: Callable[[int, int], list], page_size: int) -> Iterator:
    """Lazily yield every item from a paginated API.

    fetch_page(offset, limit) returns a list of at most `limit` items. Keep fetching
    (offset 0, page_size, 2*page_size, ...) until a page comes back shorter than page_size.
    It must be LAZY: taking the first 3 items with page_size=10 should call fetch_page only once.
    """
    raise NotImplementedError


def batched(items: Iterable, n: int) -> Iterator[tuple]:
    """Yield tuples of up to n items: list(batched("abcde", 2)) == [("a","b"), ("c","d"), ("e",)].
    Must work on any iterable, including generators (so don't use len() or slicing)."""
    raise NotImplementedError


def error_codes(lines: Iterable[str]) -> Iterator[int]:
    """Pipeline over log lines like "2024-01-01 ERROR 503 upstream timeout".
    Yield the integer status code of every ERROR line, skipping blank lines. Use generator expressions."""
    raise NotImplementedError


def managed_resource(log: list[str]) -> Iterator[str]:
    """A FastAPI-style yield dependency: append "open" to log, yield "resource",
    and ALWAYS append "close" afterwards, even if the consumer raised an error at the yield."""
    raise NotImplementedError
