# P1 · Values, strings, truthiness, `None`

> Python will feel familiar after JS, but a few defaults are different: **indentation is syntax**, there's **no `undefined`**, `==` never coerces types, and integers have no size limit.

## 🧠 Concepts

### JS → Python cheat sheet
| JS / TS | Python |
|---|---|
| `let x = 1` / `const` | `x = 1` (no keyword, no const; use UPPER_CASE by convention) |
| `null` / `undefined` | `None` (only one) |
| `true` / `false` | `True` / `False` |
| `&&` `\|\|` `!` | `and` `or` `not` |
| `===` | `==` (no coercion: `1 == "1"` is `False`) |
| `Object.is(a, b)` (identity) | `a is b` (use it for `None`: `x is None`) |
| `` `Hi ${name}` `` | `f"Hi {name}"` |
| `str.length` | `len(s)` |
| `Math.floor(7 / 2)` | `7 // 2` (floor division); `7 / 2` is always a float `3.5` |
| `2 ** 10` | `2 ** 10` |
| `parseInt("42")` | `int("42")` (raises `ValueError` on bad input; no `NaN`) |
| `x ?? y` | `y if x is None else x` (no `??` operator) |
| `cond ? a : b` | `a if cond else b` |
| `// comment` | `# comment` |
| `typeof x === "string"` | `isinstance(x, str)` |

### Truthiness
Falsy values: `None`, `False`, `0`, `0.0`, `""`, and **empty containers** (`[]`, `{}`, `set()`, `()`). Unlike JS, an **empty list is falsy**, so `if items:` means "is non-empty".

> Gotcha: `if not value:` treats `0` and `""` the same as `None`. When `0` is a valid value, write `if value is None:`.

### Strings
- They're immutable, like in JS. Single and double quotes are the same. Triple quotes `"""..."""` give multi-line strings.
- Methods: `.strip()`, `.lower()`, `.upper()`, `.title()`, `.split()`, `"-".join(parts)`, `.replace()`, `.startswith()`, `.isdigit()`, `.isalnum()`.
- Slicing: `s[0]`, `s[-1]` (last), `s[1:4]`, `s[::-1]` (reversed).
- f-string format specs: `f"{price:.2f}"` gives 2 decimals, `f"{n:,}"` adds thousands separators, `f"{x:>8}"` right-aligns, and `f"{value!r}"` uses repr. `f"{name=}"` prints `name='Ada'`, which is handy for debugging.

### Errors instead of `NaN`
```python
try:
    n = int(text)
except ValueError:
    n = 0
```

## 🏋️ Exercise
Implement the functions in `exercise.py`. Each docstring includes examples.

```bash
python check.py p1        # or: python check.py p1 -v
```
To experiment, start a REPL (`python`) or run `python -i lessons/p1_basics/exercise.py`.

## 💼 Interview angle
- *"`is` vs `==`?"*: `==` compares values (it calls `__eq__`), and `is` compares identity. Use `is` only for singletons such as `None`, `True` and `False`.
- *"Why `x is None` and not `x == None`?"*: a class can override `__eq__`, and `is` is faster and always means "this is the None object".
- *"What's falsy in Python?"*: `None`, `False`, zeros, and empty strings or containers. Mention the `0` vs `None` gotcha.
- *"Are Python ints limited to 64 bits?"*: no, they have arbitrary precision. Floats are IEEE-754 doubles, so `0.1 + 0.2 != 0.3` just like in JS. Use `decimal.Decimal` for money, or store integer cents.
