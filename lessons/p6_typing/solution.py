"""P6 reference solution."""
import inspect
import types
import typing
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Iterable, NotRequired, Protocol, TypedDict, TypeVar, runtime_checkable

T = TypeVar("T")


def first(items: list[T]) -> T | None:
    return items[0] if items else None


class UserDict(TypedDict):
    id: int
    name: str
    email: NotRequired[str]


@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...


def close_all(things: Iterable[object]) -> int:
    closed = 0
    for thing in things:
        if isinstance(thing, Closeable):  # structural check: "has a close() method"
            thing.close()
            closed += 1
    return closed


@dataclass(frozen=True)
class Range:
    lo: float
    hi: float


class ValidationFailed(Exception):
    def __init__(self, errors: list[dict]):
        super().__init__(f"{len(errors)} validation error(s)")
        self.errors = errors


_TRUE, _FALSE = {"true", "1", "yes"}, {"false", "0", "no"}


def _unwrap(hint) -> tuple[type, list, bool]:
    """Return (base_type, metadata, allows_none) for hints like Annotated[int | None, Range(..)]."""
    metadata: list = []
    if typing.get_origin(hint) is Annotated:
        hint, *metadata = typing.get_args(hint)
    allows_none = False
    if typing.get_origin(hint) in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        allows_none = len(args) < len(typing.get_args(hint))
        hint = args[0]
    return hint, metadata, allows_none


def _convert(raw: str, base: type):
    if base is bool:
        low = raw.lower()
        if low in _TRUE:
            return True
        if low in _FALSE:
            return False
        raise ValueError(raw)
    return base(raw)


def call_with_query(fn: Callable[..., Any], query: dict[str, str]) -> Any:
    hints = typing.get_type_hints(fn, include_extras=True)
    kwargs, errors = {}, []
    for name, param in inspect.signature(fn).parameters.items():
        base, metadata, allows_none = _unwrap(hints.get(name, str))
        if name not in query:
            if param.default is not inspect.Parameter.empty:
                kwargs[name] = param.default
            elif allows_none:
                kwargs[name] = None
            else:
                errors.append({"field": name, "error": "missing"})
            continue
        try:
            value = _convert(query[name], base)
        except ValueError:
            errors.append({"field": name, "error": "invalid"})
            continue
        if any(isinstance(m, Range) and not (m.lo <= value <= m.hi) for m in metadata):
            errors.append({"field": name, "error": "out_of_range"})
            continue
        kwargs[name] = value
    if errors:
        raise ValidationFailed(errors)
    return fn(**kwargs)
