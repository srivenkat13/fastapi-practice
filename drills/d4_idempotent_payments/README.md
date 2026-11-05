# D4 · Drill: idempotent payments (⏱ 30 min)

> "A user double-clicks Pay, and mobile clients retry on timeouts. Make sure we never charge twice." This tests whether you can see the **race**, not only the happy-path retry.

## Brief
Follow the requirements in the `exercise/main.py` docstring: required Idempotency-Keys, replayed responses, 409 for a key reused with a different body, **exactly one charge for 5 concurrent duplicates**, refunds that can't over-refund (even concurrently), and keys scoped per endpoint.
```bash
python check.py d4
```

## What interviewers listen for
- **Check-then-act is a race.** "If the key exists, return it, otherwise charge" fails when two requests both check before either stores. You need a lock per key (in-process `asyncio.Lock` here, a Redis `SET NX` lock or an `INSERT ... ON CONFLICT DO NOTHING` row in production) **or** a DB unique constraint on the key.
- **What to store**: a fingerprint of the request plus the response status and body, with a TTL (Stripe keeps them 24h).
- **What not to store**: validation errors and 5xx responses, so the client can fix the request or retry.
- **Scoping**: keys are per endpoint and per merchant or user.
- **Money**: integer minor units, never floats. Refund totals are guarded under a lock, or with `UPDATE payments SET refunded = refunded + :x WHERE id = :id AND refunded + :x <= amount`.
- **Gateway calls**: pass your own idempotency key **downstream** to the payment provider too. That's end-to-end idempotency.
