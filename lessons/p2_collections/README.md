# P2 · Lists, dicts, sets, tuples, comprehensions

> JSON in a FastAPI app becomes Python `dict`s and `list`s. Being fluent with collections and comprehensions is what makes Python code short and readable.

## 🧠 Concepts

| Type | Literal | JS analogue | Notes |
|---|---|---|---|
| `list` | `[1, 2, 3]` | Array | mutable, ordered |
| `tuple` | `(1, 2)` or `1, 2` | a frozen array | immutable; hashable if its contents are, so it can be a dict key |
| `dict` | `{"a": 1}` | object / `Map` | keys keep insertion order; keys must be hashable |
| `set` | `{1, 2}` (`set()` for empty, since `{}` is a dict) | `Set` | O(1) membership; `\|` union, `&` intersection, `-` difference |

### Everyday operations
```python
items.append(x); items.extend(more); items.pop(); len(items); x in items
items[-1]; items[1:3]; sorted(items, key=lambda u: u["age"], reverse=True)
d["k"]                # KeyError if missing (no undefined!)
d.get("k", default)   # safe read
d.setdefault("k", []).append(v)
{**a, **b}            # merge (like {...a, ...b}); also a | b
for key, value in d.items(): ...
for i, item in enumerate(items): ...     # like items.forEach((item, i) => ...)
for a, b in zip(xs, ys): ...
first, *rest = items                     # destructuring
```

### Comprehensions replace map/filter
```python
[u["name"] for u in users if u["active"]]          # users.filter(...).map(...)
{u["id"]: u for u in users}                         # index by id (Object.fromEntries)
{tag for post in posts for tag in post["tags"]}     # flatMap into a set
```

### `collections` helpers
- `Counter(words).most_common(3)`
- `defaultdict(list)`: missing keys start as `[]`, which makes grouping a one-liner
- `deque`: O(1) appends and pops at both ends (queues)

### Copying & mutation gotchas
- `b = a` doesn't copy anything; both names point at the same list.
- `a.copy()` / `list(a)` / `{**d}` are **shallow** copies. `copy.deepcopy` copies nested data too.
- `sort()` sorts in place and returns `None`. `sorted()` returns a new list.

## 🏋️ Exercise
Implement the functions in `exercise.py`. They work on "API-like" data (lists of dicts).
```bash
python check.py p2
```

## 💼 Interview angle
- *"List vs tuple?"*: a list is mutable. A tuple is immutable, hashable (so it works as a dict key or in a set), and used for fixed-shape records.
- *"Time complexity of `x in list` vs `x in set`?"*: O(n) vs O(1) on average. Convert to a set when you test membership repeatedly.
- *"Why can't a list be a dict key?"*: it's mutable, so it isn't hashable.
- *"Are dicts ordered?"*: yes. Insertion order is guaranteed since Python 3.7.
- *"Shallow vs deep copy?"*: a shallow copy shares nested objects.
