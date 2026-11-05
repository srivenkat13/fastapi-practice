# R2 · Caching: cache-aside, TTLs, invalidation, stampedes, HTTP caching

> "There are only two hard things in computer science: cache invalidation and naming things." This lesson implements the patterns real systems use with **Redis**. To keep it install-free you'll build a Redis-shaped in-memory cache, and the README shows the one-line swap.

## 🧠 Concepts

### Where caches live
| Layer | Example | Controlled by |
|---|---|---|
| Browser | `Cache-Control: private, max-age=60` | response headers |
| CDN / reverse proxy | Cloudflare, Fastly, nginx | `Cache-Control: public, s-maxage`, `Vary`, ETag (F15) |
| Application | Redis / Memcached / in-process LRU | your code (this lesson) |
| Database | buffer pool, materialized views | DB config / SQL |

### Cache-aside (lazy loading), the default pattern
```python
value = await redis.get(key)
if value is None:                       # miss
    value = await db.load(...)
    await redis.set(key, value, ex=60)  # TTL is a safety net for missed invalidations
return value
```
On **writes**: update the DB, then **delete** the key. Don't update it, because two racing writers can leave stale data. Other patterns: write-through (write the cache and DB together), write-behind (write the cache, flush to the DB asynchronously, which risks losing data), and refresh-ahead.

### Things that go wrong
- **Stampede / thundering herd**: a hot key expires and 1,000 requests hit the DB at once. Fixes: **single-flight** locking (implemented here; in Redis, `SET lock NX PX`), refreshing early with jittered TTLs, or serve-stale-while-revalidating.
- **Penetration**: repeated lookups for IDs that don't exist always miss. Fix: **negative caching** (cache `None` briefly) or a Bloom filter.
- **Stale data**: invalidation was missed somewhere, so use TTLs as a backstop, and version keys (`v3:product:1`) to bust everything when the schema changes.
- **In-process caches** (`functools.lru_cache`, dicts) aren't shared between workers or pods and grow without bound. Fine for config and immutable data, not for user data.

### HTTP caching headers
```
Cache-Control: public, max-age=60, stale-while-revalidate=30   ← CDN- and browser-cacheable catalog
Cache-Control: private, no-store                               ← user-specific / sensitive
Vary: Accept-Encoding, Authorization                           ← the cache key includes these headers
```

### Swapping in Redis
```python
import json, redis.asyncio as redis
r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
await r.set("product:1", json.dumps(product), ex=60)
cached = await r.get("product:1")         # None if absent → json.loads(cached) otherwise
await r.delete("product:1")
```
Create the client in the **lifespan** (F13) and inject it with a dependency, the same way `get_cache` works here.

## 🏋️ Exercise
1. `cache.py`: `InMemoryCache` (TTL with an injectable clock, a `MISSING` sentinel, per-key locks) and `get_or_load` (cache-aside with single-flight).
2. `main.py`: a singleton `get_cache`, a cached `GET /products/{id}` with an `X-Cache` header and negative caching, invalidation on `PUT`, and Cache-Control headers.
```bash
python check.py r2
```

## 💼 Interview angle
- *"How would you cache a product page?"*: CDN-cache the public parts (Cache-Control/ETag), cache-aside in Redis for data with TTL plus invalidation on writes, and never share-cache user-specific data.
- *"How do you prevent a cache stampede?"*: single-flight or a distributed lock, early refresh with jitter, stale-while-revalidate, and request coalescing at the CDN.
- *"Cache invalidation strategies?"*: TTL-only (simple, bounded staleness), delete on write, event-driven (CDC/outbox → invalidate), and versioned keys.
- *"Redis vs Memcached?"*: Redis has data structures, persistence, pub/sub, Lua and streams. Memcached is a simple multithreaded key/value store. Redis is usually the default.
- *"What's the risk of caching None?"*: entries for IDs that are created later keep returning not-found, so use a short TTL and invalidate on create.
