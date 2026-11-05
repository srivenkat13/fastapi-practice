# R4 · Production config, Docker, workers

> "It works on my machine" isn't something you can ship. This lesson covers the gap between `run.py` and production: config that **fails fast**, safe defaults (no public docs, security headers, trusted hosts), and a container image a reviewer would approve.

## 🧠 Concepts

### Running FastAPI in production
```
client → load balancer / ingress (TLS) → reverse proxy (optional: nginx) → N worker processes (uvicorn) → your app
```
- `fastapi run main.py --workers 4` (or `uvicorn main:app --workers 4`, or `gunicorn -k uvicorn.workers.UvicornWorker -w 4`).
- **Workers ≈ CPU cores** for async apps. Each worker is a separate process with its own memory, pools and in-process caches (R2!).
- In Kubernetes you often run **1 worker per container** and scale with replicas, so the orchestrator handles restarts and scaling.
- `--proxy-headers` trusts `X-Forwarded-For/Proto` from the load balancer, which gives correct client IPs and `https` URLs. Only enable it behind a proxy you trust.
- Graceful shutdown: SIGTERM, then finish in-flight requests, then the lifespan shutdown runs. Set `terminationGracePeriodSeconds` to more than your longest request.

### Config: 12-factor and fail fast
- All config comes from the **environment**. The same image runs in dev, staging and prod.
- Validate at boot (pydantic-settings validators): no default secrets, no `*` hosts in prod.
- Secrets come from a secret manager or orchestrator secrets as env vars or files. Never bake them into images or git.

### Secure defaults
| Setting | Why |
|---|---|
| Docs disabled (or behind auth) in prod | `/openapi.json` is a map of your attack surface |
| `TrustedHostMiddleware` | blocks Host-header attacks |
| `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy` | browser hardening |
| `Strict-Transport-Security` | forces HTTPS (prod only) |
| `debug=False` | no tracebacks in responses |

### A good Dockerfile
1. A **slim** base image (`python:3.13-slim`), which is hundreds of MB smaller.
2. Copy `requirements.txt` and install **before** copying the source, so the dependency layer is cached.
3. `pip install --no-cache-dir` keeps pip's cache out of the image.
4. A **non-root `USER`**, so a container escape doesn't start as root.
5. A production CMD: `0.0.0.0`, workers, no `--reload`.
6. `HEALTHCHECK` (or k8s probes from R3).
7. `.dockerignore`: keep `.venv`, `.git`, `.env` and caches out of the image (size **and** secrets).
Next steps: multi-stage builds (compile wheels in a builder stage), `uv` for fast installs, pinned digests, image scanning (Trivy/Grype).

## 🏋️ Exercise
1. `settings.py`: typed `Settings` with prod guards.
2. `app.py`: an app factory with prod-only docs hiding, trusted hosts, HSTS, plus security headers and `/version`.
3. `Dockerfile` and `.dockerignore`: fix every issue the tests list.
```bash
python check.py r4
# if you have Docker (optional):
cp lessons/r4_deployment/solution/.dockerignore .dockerignore
docker build -f lessons/r4_deployment/solution/Dockerfile -t fastapi-practice . && docker run -p 8000:8000 fastapi-practice
```

## 💼 Interview angle
- *"How do you deploy a FastAPI app?"*: a container image, uvicorn workers (or k8s replicas), behind a load balancer with TLS, config from env and a secret manager, health probes, CI/CD with migrations before rollout, and blue-green or rolling deploys.
- *"How many workers?"*: about the number of cores for async I/O work. Watch memory per worker. In k8s, prefer 1 per pod and scale horizontally.
- *"How do you handle secrets?"*: a secret manager or k8s secrets injected at runtime, never in images, git or logs (`SecretStr`), and rotate them.
- *"Zero-downtime deploys?"*: rolling or blue-green, readiness probes, graceful shutdown, and backwards-compatible DB migrations (expand, migrate, contract).
- *"Why non-root containers?"*: least privilege. Root inside a container plus a kernel bug can mean root on the host.
