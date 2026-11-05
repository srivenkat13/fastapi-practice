# D1 · Drill: rate-limit dependency (⏱ 25 min)

> Interview format: "Add rate limiting to this API." Set a timer, talk out loud while you work (in a real interview you would), and then compare with `solution/`.

## Brief
Implement `RateLimiter` in `exercise/main.py` as a **callable class used as a dependency**, then apply `search_limiter` to `GET /search` and `export_limiter` to `POST /export`. The docstring has the rules, and the tests have the edge cases (sliding window, per-key buckets, Retry-After).

```bash
python check.py d1
```

## What interviewers listen for
- **Algorithm choice**: a fixed window allows 2× bursts at the boundary, a sliding log is exact but O(limit) memory per key, a sliding counter approximates it, and a token bucket allows bursts with a steady refill.
- **Key choice**: API key or user ID, then IP as a fallback (IPs behind NAT are shared).
- **Distributed**: in-memory state is per worker. In production, use Redis (`ZADD`/`ZREMRANGEBYSCORE`/`ZCARD` in a Lua script or `MULTI`, or `INCR`+`EXPIRE` for a fixed window).
- **Testability**: an injectable clock, not `time.sleep` in tests.
- **Response**: 429 + `Retry-After`, plus limit headers. Rate-limit login endpoints the hardest.
