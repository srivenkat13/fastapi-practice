"""P1 exercise: replace each `raise NotImplementedError` with a real implementation."""


def greet(name: str, excited: bool = False) -> str:
    """Return a greeting using an f-string. Strip surrounding whitespace from `name`.

    greet("Ada")               -> "Hello, Ada."
    greet("  Ada ", True)      -> "Hello, Ada!"
    """
    raise NotImplementedError


def initials(full_name: str) -> str:
    """Upper-case initials followed by dots. Extra spaces should be ignored.

    initials("ada lovelace")          -> "A.L."
    initials("  grace  brewster hopper ") -> "G.B.H."
    initials("")                      -> ""
    """
    raise NotImplementedError


def is_blank(value) -> bool:
    """True for None, "" and whitespace-only strings. False for everything else, *including 0 and False*.

    is_blank(None) -> True     is_blank("  ") -> True
    is_blank(0)    -> False    is_blank("x")  -> False
    """
    raise NotImplementedError


def safe_int(text: str, default: int = 0) -> int:
    """Convert text to int; return `default` if it isn't a valid integer (Python has no NaN for ints).

    safe_int("42") -> 42    safe_int(" 7 ") -> 7    safe_int("4.2") -> 0    safe_int("abc", -1) -> -1
    """
    raise NotImplementedError


def format_price(cents: int) -> str:
    """Format integer cents as dollars with thousands separators and 2 decimals.

    format_price(1250)     -> "$12.50"
    format_price(123456789) -> "$1,234,567.89"
    format_price(-500)     -> "-$5.00"
    """
    raise NotImplementedError


def slugify(title: str) -> str:
    """Lower-case; runs of non-alphanumeric characters become a single "-"; no leading/trailing "-".

    slugify("Hello, World!")        -> "hello-world"
    slugify("  FastAPI  &  Python 3 ") -> "fastapi-python-3"
    """
    raise NotImplementedError


def middle(items: str) -> str:
    """Use slicing: return the string without its first and last characters, reversed.

    middle("abcde") -> "dcb"     middle("ab") -> ""
    """
    raise NotImplementedError
