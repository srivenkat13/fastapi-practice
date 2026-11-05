# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then the source (changes often, so it gets cheap rebuilds).
COPY . .

# Never run as root inside the container.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

# Bind 0.0.0.0 (reachable from outside the container), several worker processes, trust the proxy's X-Forwarded-* headers.
CMD ["fastapi", "run", "lessons/r4_deployment/solution/main.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers"]
