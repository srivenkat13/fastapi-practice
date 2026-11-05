import copy

from support import target

m = target(__file__)
USERS = m.USERS


def test_active_names():
    assert m.active_names(USERS) == ["Ada", "Grace", "Guido"]


def test_index_by_id():
    idx = m.index_by_id(USERS)
    assert set(idx) == {1, 2, 3, 4}
    assert idx[3]["name"] == "Grace"


def test_group_by_team():
    assert m.group_by_team(USERS) == {"core": ["Ada", "Grace"], "kernel": ["Linus"], "lang": ["Guido"]}


def test_all_skills():
    assert m.all_skills(USERS) == ["c", "cobol", "git", "math", "python"]


def test_top_skills():
    assert m.top_skills(USERS, 2) == [("python", 3), ("c", 2)]


def test_merge_settings_is_pure():
    defaults, overrides = {"a": 1, "b": 2}, {"b": 3, "c": None}
    before = (copy.deepcopy(defaults), copy.deepcopy(overrides))
    assert m.merge_settings(defaults, overrides) == {"a": 1, "b": 3}
    assert (defaults, overrides) == before


def test_chunk():
    assert m.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert m.chunk([], 3) == []


def test_sort_users():
    original = [u["name"] for u in USERS]
    assert [u["name"] for u in m.sort_users(USERS)] == ["Grace", "Ada", "Linus", "Guido"]
    assert [u["name"] for u in USERS] == original, "sort_users must not mutate its input"
