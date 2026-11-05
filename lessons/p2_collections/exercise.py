"""P2 exercise. Prefer comprehensions and the `collections` module over manual loops where it reads well."""

USERS = [
    {"id": 1, "name": "Ada", "team": "core", "active": True, "skills": ["python", "math"]},
    {"id": 2, "name": "Linus", "team": "kernel", "active": False, "skills": ["c", "git"]},
    {"id": 3, "name": "Grace", "team": "core", "active": True, "skills": ["cobol", "python"]},
    {"id": 4, "name": "Guido", "team": "lang", "active": True, "skills": ["python", "c"]},
]


def active_names(users: list[dict]) -> list[str]:
    """Names of active users, in original order.  -> ["Ada", "Grace", "Guido"]"""
    raise NotImplementedError


def index_by_id(users: list[dict]) -> dict[int, dict]:
    """{id: user} for fast lookups (a dict comprehension)."""
    raise NotImplementedError


def group_by_team(users: list[dict]) -> dict[str, list[str]]:
    """{team: [names...]} preserving order.  -> {"core": ["Ada", "Grace"], "kernel": ["Linus"], ...}"""
    raise NotImplementedError


def all_skills(users: list[dict]) -> list[str]:
    """Every distinct skill across users, sorted alphabetically."""
    raise NotImplementedError


def top_skills(users: list[dict], n: int) -> list[tuple[str, int]]:
    """The n most common skills as (skill, count) tuples, most common first. Hint: collections.Counter."""
    raise NotImplementedError


def merge_settings(defaults: dict, overrides: dict) -> dict:
    """Return a NEW dict: defaults updated with overrides, ignoring overrides whose value is None.
    Must not mutate either argument.

    merge_settings({"a": 1, "b": 2}, {"b": 3, "c": None}) -> {"a": 1, "b": 3}
    """
    raise NotImplementedError


def chunk(items: list, size: int) -> list[list]:
    """Split into consecutive chunks (pagination!).  chunk([1,2,3,4,5], 2) -> [[1,2],[3,4],[5]]"""
    raise NotImplementedError


def sort_users(users: list[dict]) -> list[dict]:
    """New list sorted by team ascending, then name descending. Hint: sort twice (stable sort) or a tuple key."""
    raise NotImplementedError
