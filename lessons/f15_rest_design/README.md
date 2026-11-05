# F15 · REST design: versioning, ETags, idempotency, rate limits, OpenAPI

> Senior backend interviews go past "can you build CRUD" to "can you design an API that survives retries, concurrent edits, abusive clients and breaking changes?" These HTTP-level patterns answer that question.

## 🧠 Concepts

### Resource design basics
- Use nouns and plurals: `/orders/{id}/items`, not `/getOrderItems`. Express actions as sub-resources or state changes: `POST /orders/{id}/cancel` is acceptable when the action doesn't map to CRUD.
- Methods carry meaning. **Safe** methods (GET, HEAD) change nothing. **Idempotent** methods (GET, PUT, DELETE) give the same end state however many times they're repeated. POST and PATCH aren't idempotent unless you make them so.
- Be consistent: plural nouns, `snake_case` or `camelCase` (pick one), ISO-8601 UTC timestamps, money as integer minor units or decimal strings (never floats), and one error envelope (F05).

### Versioning & evolution
| Strategy | Example | Notes |
|---|---|---|
| URL prefix | `/v1/...`, `/v2/...` | the most common, explicit and easy to route, here via `include_router` |
| Header / media type | `Accept: application/vnd.shop.v2+json` | cleaner URLs, harder to test and cache |
| No versions, additive only | add fields, never remove | works well with an expand/contract discipline |
Announce deprecation with the `Deprecation` and `Sunset` headers and `Link: <...>; rel="successor-version"`, and track which clients still call v1.

### Caching & concurrency with ETags
```
GET /v1/products/1            → 200, ETag: "a1b2"
GET ... If-None-Match: "a1b2" → 304 Not Modified (no body: saves bandwidth)
PUT ... If-Match: "a1b2"      → 200 and a new ETag | 412 Precondition Failed if someone changed it first
PUT without If-Match          → 428 Precondition Required (optional strictness)
```
`If-Match` is **optimistic concurrency control**. It prevents the *lost update* where two editors overwrite each other. The DB equivalent is a `version` column: `UPDATE ... WHERE id=? AND version=?`.

### Idempotency keys (retries without double charges)
Networks fail **after** the server has done the work. The client retries with the same `Idempotency-Key`:
1. First request: process it, then store `key → (request fingerprint, status, response)`.
2. Same key with the same body: **replay** the stored response, with no new side effects.
3. Same key with a different body: 422.
4. In production: store keys in Redis or the DB with a TTL (24h), and handle **concurrent** duplicates with a lock or a unique insert (drill D4).
This is how Stripe's API works.

### Rate limiting
Algorithms: **fixed window** (simple, bursty at edges), **sliding window log/counter**, **token bucket** (allows bursts, then a steady rate). Respond with `429` plus `Retry-After`, and advertise `X-RateLimit-Limit/Remaining`. In production it lives in **Redis** (shared across workers, using an atomic `INCR`+`EXPIRE` or a Lua script) or at the gateway (nginx, Cloudflare, API Gateway). Libraries: `slowapi`, `fastapi-limiter`.

### OpenAPI as a product
- `generate_unique_id_function` gives readable `operationId`s, which become method names in generated clients (`api.v1GetProduct()`).
- Document error responses: `responses={404: {"model": ErrorOut}}`.
- Use tags, summaries and examples in your models. The spec **is** the contract with the frontend team, so check it for breaking changes in CI (`oasdiff`).

## 🏋️ Exercise
Implement everything marked TODO in `exercise/main.py`: deprecation headers, a v2 router, ETag/304, If-Match (428/412), idempotency keys, a rate-limit dependency with an injectable clock, and custom operationIds.
```bash
python check.py f15
```

## 💼 Interview angle
- *"A client times out creating a payment and retries. How do you prevent double charges?"*: idempotency keys with a stored response, a request fingerprint, a TTL, and a lock or unique constraint for concurrent duplicates.
- *"Two users edit the same record. How do you avoid lost updates?"*: ETag/If-Match (412) or a version column (409), or pessimistic locks (`SELECT ... FOR UPDATE`) for short critical sections.
- *"Design a rate limiter."*: compare token bucket and windows, use Redis atomic ops shared across instances, choose the key (user, API key or IP), and return 429 with Retry-After.
- *"How do you version and deprecate an API?"*: prefer additive changes, use a new major version for breaking changes, send Deprecation/Sunset headers, use telemetry to see who still calls v1, and keep the spec diff in CI.
- *"Which HTTP methods are idempotent?"*: GET, HEAD, PUT, DELETE and OPTIONS. Not POST, and not necessarily PATCH.
