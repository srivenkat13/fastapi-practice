# D2 · Drill: search + cursor pagination (⏱ 30 min)

> A favourite take-home and live-coding task: "Our feed endpoint duplicates items when new posts arrive. Fix it."

## Brief
Rewrite `GET /articles` in `exercise/main.py` from page numbers to **keyset (cursor) pagination** with search and tag filters. The docstring has the contract, and the tests check gaps, duplicates, ties, filters, and stability under inserts.

```bash
python check.py d2
```

## What interviewers listen for
- **Why offset breaks**: an insert at the top shifts every row down, so page 2 repeats an item. Deleting a row makes you skip one. Deep offsets scan and discard N rows.
- **A total order**: sort by `(published_at DESC, id DESC)`. Without the unique tie-breaker, rows with equal timestamps get skipped or duplicated.
- **The keyset condition**: `WHERE (published_at, id) < (:p, :id)` uses a composite index `(published_at DESC, id DESC)`, so every page costs the same.
- **Opaque cursors**: base64-encode the position so clients don't build cursors themselves. You can sign it (HMAC) to prevent tampering, and include the filters to reject mismatched reuse.
- The **limit + 1** trick tells you whether there's a next page without a COUNT query.
- The trade-off: there's no "jump to page 7" and no total count (or an expensive one). That's why feeds use cursors and admin tables use offsets.
