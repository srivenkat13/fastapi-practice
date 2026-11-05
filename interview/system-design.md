# Backend system design: FastAPI-flavoured scenarios

> At 6+ years, expect at least one design round. Use the same structure every time, and draw boxes. Each scenario lists the points interviewers look for, with pointers to lessons where you've built that piece.

## Framework for any design question (≈45 min)
1. **Clarify** (5 min): users, core flows, scale (RPS, data size), latency and consistency needs, what's out of scope.
2. **API first** (5 min): endpoints, payloads, status codes, pagination, idempotency. You're strong here, so lead with it.
3. **Data model** (5 min): entities, relationships, indexes, access patterns.
4. **High-level architecture** (10 min): clients → CDN → LB → stateless FastAPI pods → Postgres / Redis / queue / object storage.
5. **Deep dives** (15 min): the hard parts: hot paths, consistency, failure modes, scaling.
6. **Operations** (5 min): observability, deploys, security, cost.

---

## 1. URL shortener
- API: `POST /links {url}` → 201 `{code}`; `GET /{code}` → 301/302. Make creation idempotent per user+URL if required.
- Codes: base62 of an ID from a sequence or Snowflake (no collisions) vs random with a uniqueness check.
- Reads vastly outnumber writes, so: **Redis cache-aside** for code → url, CDN for redirects, negative caching for unknown codes (R2).
- Analytics: do **not** write to the DB on every redirect. Publish an event to a queue or stream and aggregate asynchronously.
- Rate-limit creation (abuse), validate URLs (open-redirect and phishing lists).

## 2. Notifications service (email, push, in-app)
- API: `POST /notifications` (internal, idempotency key), `GET /me/notifications?cursor=` (D2), `PATCH .../read`.
- Fan-out through a **queue** (SQS, Kafka, Celery). The API returns **202 Accepted**.
- Workers per channel, retries with exponential backoff and a dead-letter queue, provider idempotency keys.
- User preferences and quiet hours, templating, rate limits per user.
- Real-time in-app delivery: WebSocket or SSE gateway plus **Redis pub/sub** across pods (F14).

## 3. Rate limiter as a service
- Token bucket in Redis using a Lua script (atomic), keyed by `tenant:user:route`, as covered in F15 and D1.
- Placement: gateway (nginx, Envoy, API Gateway) vs a middleware/dependency in the app.
- Return 429 + Retry-After and limit headers. Decide whether to fail open or fail closed when Redis is down.
- Multi-region: local counters with async sync, or accept approximate limits.

## 4. File upload & processing (avatars, documents)
- **Presigned S3 URLs**: the client uploads straight to S3, so the API never streams large bodies (F14).
- An S3 event → queue → worker validates (magic bytes, AV scan), creates thumbnails, and updates the DB status (`pending → ready/failed`).
- The client polls `GET /uploads/{id}` or subscribes through SSE.
- Size and type limits, private buckets, signed download URLs with expiry, CDN in front.

## 5. Payments / orders (consistency-critical)
- **Idempotency keys** end to end: client → API → payment provider (F15, D4).
- Order state machine (`pending → paid → shipped / refunded`), with transitions in transactions.
- **Outbox pattern**: write the order and an "event" row in the same DB transaction, then a relay publishes it to the bus. That avoids the dual-write problem.
- Webhooks from the provider: verify signatures, store event IDs to de-duplicate, process asynchronously.
- Money as integer minor units, an audit log, and reconciliation jobs.

## 6. Real-time collaborative task board (an extension of the capstone)
- REST for CRUD (C1), plus WebSocket per project room for live updates.
- Multiple pods: Redis pub/sub channel per project. Clients reconnect and **catch up** with `GET /events?since=cursor`.
- Conflict handling: ETag/If-Match (F15) or last-write-wins per field. CRDTs are for text-level collaboration.
- Presence via Redis keys with a TTL and heartbeats.

## 7. Serving an ML model or LLM feature behind FastAPI (a very common question for Python roles)
- Load the model once per worker in the **lifespan** (F13). Watch memory × workers.
- CPU/GPU-bound inference must not block the event loop: use a process pool, a dedicated inference server (Triton, vLLM, TGI), or a queue for batch jobs.
- **Stream tokens** with SSE or `StreamingResponse` (F14), and set timeouts and cancellation when the client disconnects.
- Caching identical prompts (R2), rate limiting per user (D1), cost tracking, request logging with redaction (R3).
- Evaluate and monitor quality, latency (p50/p99) and errors, and keep a fallback model.

---

## Scaling cheat sheet
| Bottleneck | Levers |
|---|---|
| App CPU | more workers or pods (stateless), profile hot paths, offload CPU work |
| Event loop blocked | `def` endpoints / `to_thread`, async drivers (F12) |
| DB connections | pool sizing, PgBouncer, fewer workers × pool size |
| DB reads | indexes, eager loading (F08), read replicas, caching (R2) |
| DB writes | batching, queues, partitioning or sharding (last resort) |
| Slow upstreams | timeouts, retries with backoff, circuit breakers, cached fallbacks (F12) |
| Large payloads | pagination (F09, D2), streaming (F14), compression (F13), CDN |
