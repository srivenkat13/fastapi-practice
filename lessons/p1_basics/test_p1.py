from support import target

m = target(__file__)


def test_greet():
    assert m.greet("Ada") == "Hello, Ada."
    assert m.greet("  Ada ", True) == "Hello, Ada!"


def test_initials():
    assert m.initials("ada lovelace") == "A.L."
    assert m.initials("  grace  brewster hopper ") == "G.B.H."
    assert m.initials("") == ""


def test_is_blank_uses_none_checks_not_truthiness():
    assert m.is_blank(None) is True
    assert m.is_blank("") is True
    assert m.is_blank("   \n") is True
    assert m.is_blank(0) is False
    assert m.is_blank(False) is False
    assert m.is_blank("x") is False
    assert m.is_blank([]) is False


def test_safe_int():
    assert m.safe_int("42") == 42
    assert m.safe_int(" 7 ") == 7
    assert m.safe_int("4.2") == 0
    assert m.safe_int("abc", -1) == -1


def test_format_price():
    assert m.format_price(1250) == "$12.50"
    assert m.format_price(123456789) == "$1,234,567.89"
    assert m.format_price(0) == "$0.00"
    assert m.format_price(-500) == "-$5.00"


def test_slugify():
    assert m.slugify("Hello, World!") == "hello-world"
    assert m.slugify("  FastAPI  &  Python 3 ") == "fastapi-python-3"


def test_middle():
    assert m.middle("abcde") == "dcb"
    assert m.middle("ab") == ""
