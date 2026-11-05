"""P1 reference solution."""
import re


def greet(name: str, excited: bool = False) -> str:
    end = "!" if excited else "."  # ternary: a if cond else b
    return f"Hello, {name.strip()}{end}"


def initials(full_name: str) -> str:
    # str.split() with no argument splits on any run of whitespace and drops empties.
    return "".join(f"{part[0].upper()}." for part in full_name.split())


def is_blank(value) -> bool:
    if value is None:
        return True
    return isinstance(value, str) and value.strip() == ""


def safe_int(text: str, default: int = 0) -> int:
    try:
        return int(text)  # int() already tolerates surrounding whitespace
    except (ValueError, TypeError):
        return default


def format_price(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) / 100:,.2f}"


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def middle(items: str) -> str:
    return items[1:-1][::-1]
