# R3 · Observability: structured logs, request IDs, health checks

> At 3am, `print("here")` won't help. Production services emit **structured logs** (JSON) with a **correlation ID** on every line, expose **health endpoints** for the orchestrator, and turn crashes into a generic response the support team can look up in the logs.

## 🧠 Concepts

### The three pillars
| | What | Python tooling |
|---|---|---|
| **Logs** | discrete events ("order viewed", errors) | `logging` + a JSON formatter (or `structlog`, `loguru`) |
| **Metrics** | aggregated numbers (RPS, p99 latency, error rate) | Prometheus client, OpenTelemetry metrics |
| **Traces** | one request's path across services | **OpenTelemetry** (`opentelemetry-instrumentation-fastapi`), Jaeger, Tempo, Datadog |
Errors go to Sentry. Dashboards and alerts are built on metrics (the RED method: Rate, Errors, Duration).

### Python `logging` in 5 lines
```python
log = logging.getLogger("app.orders")          # hierarchical names: "app.orders" propagates to "app"
log.info("order viewed", extra={"order_id": 7})  # extra fields become record attributes
log.exception("failed")                          # ERROR level + the traceback (inside an except block)
```
**Loggers** produce records, **filters** enrich or drop them, **handlers** send them somewhere, and **formatters** render them. Use `%s`-style args (`log.info("x %s", v)`) rather than f-strings, so formatting is lazy and skipped when the level is off.

### Correlation IDs with `contextvars`
```python
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
token = request_id_var.set(rid)     # in the middleware
...                                 # any code in this request can call request_id_var.get()
request_id_var.reset(token)
```
`ContextVar` is the asyncio-safe version of a thread-local: concurrent requests on one event loop each see their own value. A logging **filter** stamps it onto every record, so you never pass it around by hand. Propagate it to downstream calls (the `X-Request-ID` header) for cross-service search. OpenTelemetry generalises this to `traceparent`.

### Health checks (Kubernetes vocabulary)
| Probe | Question | Failing means |
|---|---|---|
| **liveness** `/health` | is the process stuck? | restart the container. Never check the DB here, or a DB blip restarts your whole fleet |
| **readiness** `/ready` | can it take traffic now? | remove it from the load balancer until it recovers |
| startup | has it finished booting? | delay the other probes |

### Errors
Every unhandled exception should produce: one ERROR log with the traceback and the request ID, a generic 500 with the **same request ID**, and an access-log line with `status=500`. The user sends support the ID, and you find the exact traceback.

## 🏋️ Exercise
1. `observability.py`: `RequestIdFilter`, `JsonFormatter` (extra fields and exceptions included), and idempotent `configure_logging`.
2. `main.py`: middleware (request ID contextvar, response header, one access-log line per request including 500s, and crash handling with a correlated 500), `/health`, and `/ready` with injectable checks (503 when any check fails).
```bash
python check.py r3
python run.py r3 --solution   # watch JSON log lines while you call /orders/7 and /orders/13
```

## 💼 Interview angle
- *"How do you debug a production issue in a distributed system?"*: correlation or trace IDs across services, structured logs searchable by ID, metrics to find when it started, traces to see where time went, and Sentry for stack traces.
- *"Liveness vs readiness?"*: restart vs stop routing traffic. Dependency checks belong in readiness only.
- *"Why structured logging?"*: logs become queryable (`status:500 AND path:/orders*`), there's no regex parsing, and context is consistent.
- *"How does request context work in async Python?"*: through `contextvars`, which are copied per asyncio task. Thread-locals would leak between concurrent requests on one loop.
- *"What do you put in logs, and what do you keep out?"*: IDs, timings, outcomes. Keep out passwords, tokens, PII and card numbers. Redact them in the formatter.
