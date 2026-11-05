# F11 · Testing FastAPI: TestClient, overrides, fixtures (and mutation testing)

> In this lesson **you write the tests**. The grader uses **mutation testing**: your suite must pass on the real Cart API **and fail on six copies of it, each with one planted bug**. A test suite that never fails isn't protecting anything.

## 🧠 Concepts

### pytest in 60 seconds (vs Jest)
| Jest | pytest |
|---|---|
| `test('x', () => {...})` | `def test_x(): ...` |
| `expect(a).toBe(b)` | `assert a == b` (pytest rewrites asserts to show diffs) |
| `expect(() => f()).toThrow(E)` | `with pytest.raises(E): f()` |
| `beforeEach` / setup | **fixtures**: `def client(): ...` injected by parameter name |
| `test.each` | `@pytest.mark.parametrize("a, b", [(1, 2), ...])` |
| `jest.mock` | `monkeypatch`, `unittest.mock`, and with FastAPI, **`dependency_overrides`** |
| shared setup file | `conftest.py` (fixtures visible to every test below that folder) |

```python
@pytest.fixture
def client(app):                     # fixtures can depend on fixtures
    return TestClient(app)

@pytest.fixture
def db():
    session = make_session()
    yield session                     # teardown after the yield, just like FastAPI deps
    session.rollback()
```

### TestClient vs AsyncClient
```python
client = TestClient(app)                          # sync and simple; runs the ASGI app in-process
with TestClient(app) as client: ...               # also runs lifespan startup/shutdown

# async tests (e.g. you need to await other things in the same loop)
async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
    r = await ac.get("/")
```

### Control the world with dependency overrides
```python
app.dependency_overrides[get_now] = lambda: datetime(2031, 1, 1, tzinfo=timezone.utc)  # freeze time
app.dependency_overrides[get_db] = lambda: test_session
app.dependency_overrides[get_current_user] = lambda: User(id=1, role="admin")         # skip auth
```
Make time, randomness, external APIs and the current user **dependencies**, and tests get deterministic.

### Test strategy for an API
- **Most tests at the HTTP level** (TestClient): they cover routing, validation, serialization and auth together.
- **Unit tests** for pure business logic (pricing, permissions).
- **DB**: a real engine (SQLite in-memory, or Postgres in Docker/testcontainers in CI), with a transaction per test that's rolled back.
- **Edge cases**: boundaries (exactly the minimum), wrong user, missing auth, expiry, empty states, idempotency.
- Use coverage (`pytest-cov`) as a hint. Mutation testing (`mutmut`, or this lesson) measures whether the tests actually **detect** bugs.

## 📜 Cart API spec (write your tests against this)
All `/cart` endpoints require an `X-User` header (otherwise **401**). Each user has **their own** cart.
| Endpoint | Behaviour |
|---|---|
| `GET /cart` | `{"items": [{sku, qty, unit_price_cents, line_total_cents}], "subtotal_cents", "discount_cents", "total_cents", "coupon"}`, items sorted by SKU |
| `POST /cart/items` `{sku, qty}` | 201 + the cart. `qty` 1–10 (422). Unknown SKU → 404. The same SKU again **adds** to the quantity, and more than 10 in total → 409 |
| `DELETE /cart/items/{sku}` | 204, or 404 if the item isn't in the cart |
| `POST /cart/coupon` `{code}` | case-insensitive code. Unknown → 404. Invalid now → 422 with a reason. Returns the cart |

Catalog: `KB` 2500¢, `MOUSE` 1500¢, `CABLE` 300¢.
Coupons:
- `SAVE10`: 10% off, needs a subtotal of **at least** 5000¢, expires **2030-01-01T00:00Z** (invalid from that instant)
- `FLAT500`: 500¢ off. The discount never exceeds the subtotal, so the total is never negative
- `OLD20`: expired in 2020
- Coupons are re-checked whenever the cart is read. If the cart no longer qualifies, the coupon is dropped.

Time comes from the `get_now` dependency, so override it to test expiry.

## 🏋️ Exercise
Write tests in `exercise/tests_cart_api.py`, using the `client` and `app` fixtures from `conftest.py`.
```bash
python -m pytest lessons/f11_testing/exercise/tests_cart_api.py -v   # your suite on the real app
python check.py f11                                                 # mutation grading
```
The grader tells you which mutant survived. Each one corresponds to a rule in the spec.

## 💼 Interview angle
- *"How do you test a FastAPI app?"*: pytest + TestClient, fixtures in conftest, `dependency_overrides` for DB, auth and clock, and a real DB with per-test rollback. Async tests use httpx `ASGITransport`.
- *"How do you test time-dependent logic?"*: inject the clock as a dependency (or use `freezegun`/`time-machine`) and test the exact boundaries.
- *"Is 100% coverage enough?"*: no. Coverage shows what ran, not what was checked. Mutation testing shows whether tests catch bugs.
- *"Unit vs integration tests for APIs?"*: mostly HTTP-level integration tests for confidence, unit tests for dense business rules, and a few end-to-end tests against a deployed environment.
