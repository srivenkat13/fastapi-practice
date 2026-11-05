"""P6 exercise."""
import inspect  # noqa: F401
import typing  # noqa: F401
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Iterable, Protocol, TypedDict, TypeVar  # noqa: F401

T = TypeVar("T")


# 1) Generic: return the first item, or None for an empty list. Annotate it with T.
def first(items):
    raise NotImplementedError


# 2) TypedDict: id: int, name: str (both required), email: str (optional, use NotRequired).
class UserDict(TypedDict):
    pass


# 3) A runtime-checkable Protocol with a `close(self) -> None` method,
#    and close_all(): close every Closeable in `things`, skip anything that isn't one,
#    return how many were closed.
class Closeable(Protocol):
    pass


def close_all(things: Iterable[object]) -> int:
    raise NotImplementedError


# 4) A toy FastAPI.
@dataclass(frozen=True)
class Range:
    """Metadata for Annotated[int, Range(lo, hi)]: value must satisfy lo <= value <= hi."""

    lo: float
    hi: float


class ValidationFailed(Exception):
    def __init__(self, errors: list[dict]):
        super().__init__(f"{len(errors)} validation error(s)")
        self.errors = errors  # e.g. [{"field": "limit", "error": "out_of_range"}]


def call_with_query(fn: Callable[..., Any], query: dict[str, str]) -> Any:
    """Call `fn` with arguments parsed from `query` (all values are strings, like a URL query).

    For each parameter of fn:
      - hint is int / float / str / bool, possibly wrapped in `X | None` and/or Annotated[X, Range(...)]
      - present in query  -> convert: int(), float(), str; bool accepts "true/1/yes" and "false/0/no"
                             conversion failure -> {"field": name, "error": "invalid"}
                             Range violated     -> {"field": name, "error": "out_of_range"}
      - missing           -> use the default; if there's no default:
                               None if the hint allows None, else {"field": name, "error": "missing"}
    Collect ALL errors (don't stop at the first) and raise ValidationFailed(errors) if any.
    Unknown query keys are ignored.
    """
    raise NotImplementedError
