# P4 · Classes, dataclasses, exceptions, context managers

> Pydantic models, SQLAlchemy models, custom exceptions and DB sessions (`with Session() as s:`) are all classes and context managers. This lesson covers the parts you'll actually use.

## 🧠 Concepts

### Classes vs JS
```python
class Account:
    bank = "PyBank"                    # class attribute (like a static field)

    def __init__(self, owner, balance=0):   # constructor
        self.owner = owner             # `self` is explicit (it's JS's `this`)
        self._balance = balance        # leading underscore = "private by convention"

    @property                          # getter: account.balance (no parentheses)
    def balance(self):
        return self._balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._balance += amount

    @classmethod                       # alternative constructor: Account.from_dict({...})
    def from_dict(cls, data): return cls(data["owner"], data.get("balance", 0))

    @staticmethod
    def validate_iban(s): ...

    def __repr__(self): return f"Account({self.owner!r}, {self._balance})"   # debug output
    def __eq__(self, other): ...       # ==
```
- "Dunder" (double-underscore) methods hook into syntax: `__len__` for `len()`, `__iter__` for `for` loops, `__contains__` for `in`, `__getitem__` for `x[i]`, `__enter__`/`__exit__` for `with`, `__call__` to make an instance callable.
- Inheritance: `class Savings(Account):` and `super().__init__(...)`.

### Dataclasses: less boilerplate
```python
from dataclasses import dataclass, field

@dataclass(frozen=True)          # frozen = immutable and hashable
class Money:
    amount: int
    currency: str = "USD"
    tags: list[str] = field(default_factory=list)   # never a mutable default (see P3)
```
You get `__init__`, `__repr__` and `__eq__` for free. **Pydantic's `BaseModel`** looks similar but also **validates and converts** input at runtime. Dataclasses don't validate anything.

### Exceptions
```python
class DomainError(Exception): """Base for our app errors."""
class InsufficientFunds(DomainError):
    def __init__(self, needed: int):
        super().__init__(f"need {needed} more")
        self.needed = needed

try: ...
except InsufficientFunds as e: ...
except (KeyError, ValueError): ...
else: ...      # runs only if nothing was raised
finally: ...   # always runs
raise NewError("context") from original    # keeps the cause chain
```
In the FastAPI lessons you'll raise **domain errors** in your services and turn them into HTTP responses in a single place (lesson F05).

### Context managers (`with`)
They guarantee cleanup, like `try/finally`, and are used for files, DB sessions, locks and transactions.
```python
from contextlib import contextmanager

@contextmanager
def transaction(db):
    db.begin()
    try:
        yield db          # the body of the `with` block runs here
        db.commit()
    except Exception:
        db.rollback()
        raise
```

## 🏋️ Exercise
`exercise.py`: build `Money` (a frozen dataclass with `+`), a `Wallet` class with a property, dunders and a custom exception hierarchy, and a `transaction()` context manager.
```bash
python check.py p4
```

## 💼 Interview angle
- *"dataclass vs Pydantic model vs plain class?"*: a dataclass is boilerplate-free storage with no validation. Pydantic validates and coerces at runtime (use it at the edges of your system, such as HTTP and config). A plain class is for behaviour.
- *"`@classmethod` vs `@staticmethod`?"*: a classmethod receives `cls` (use it for alternative constructors and subclass-friendly code). A staticmethod is a namespaced function.
- *"What does `with` do?"*: it calls `__enter__`, and then `__exit__` even if the body raised. `__exit__` returning True swallows the exception.
- *"`__repr__` vs `__str__`?"*: repr is for developers and should be unambiguous. str is for display.
- *"How do you design exception hierarchies?"*: one base `AppError`, with specific subclasses that carry data. Catch narrow exceptions and never use a bare `except:`.
