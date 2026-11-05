"""P2 reference solution."""
from collections import Counter, defaultdict

USERS = [
    {"id": 1, "name": "Ada", "team": "core", "active": True, "skills": ["python", "math"]},
    {"id": 2, "name": "Linus", "team": "kernel", "active": False, "skills": ["c", "git"]},
    {"id": 3, "name": "Grace", "team": "core", "active": True, "skills": ["cobol", "python"]},
    {"id": 4, "name": "Guido", "team": "lang", "active": True, "skills": ["python", "c"]},
]


def active_names(users):
    return [u["name"] for u in users if u["active"]]


def index_by_id(users):
    return {u["id"]: u for u in users}


def group_by_team(users):
    groups = defaultdict(list)
    for u in users:
        groups[u["team"]].append(u["name"])
    return dict(groups)


def all_skills(users):
    return sorted({skill for u in users for skill in u["skills"]})


def top_skills(users, n):
    return Counter(skill for u in users for skill in u["skills"]).most_common(n)


def merge_settings(defaults, overrides):
    return {**defaults, **{k: v for k, v in overrides.items() if v is not None}}


def chunk(items, size):
    return [items[i : i + size] for i in range(0, len(items), size)]


def sort_users(users):
    # Python's sort is stable: sort by the secondary key first, then the primary key.
    by_name_desc = sorted(users, key=lambda u: u["name"], reverse=True)
    return sorted(by_name_desc, key=lambda u: u["team"])
