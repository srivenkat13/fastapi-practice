"""P7 reference solution."""
from typing import Callable, Iterable, Iterator


class Countdown:
    def __init__(self, start: int):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


def countdown(n: int) -> Iterator[int]:
    while n > 0:
        yield n
        n -= 1


def paginate(fetch_page: Callable[[int, int], list], page_size: int) -> Iterator:
    offset = 0
    while True:
        page = fetch_page(offset, page_size)
        yield from page
        if len(page) < page_size:
            return
        offset += page_size


def batched(items: Iterable, n: int) -> Iterator[tuple]:
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) == n:
            yield tuple(batch)
            batch = []
    if batch:
        yield tuple(batch)


def error_codes(lines: Iterable[str]) -> Iterator[int]:
    parts = (line.split() for line in lines if line.strip())
    return (int(p[2]) for p in parts if p[1] == "ERROR")


def managed_resource(log: list[str]) -> Iterator[str]:
    log.append("open")
    try:
        yield "resource"
    finally:
        log.append("close")
