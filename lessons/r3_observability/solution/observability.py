"""Structured logging with a per-request correlation ID."""
import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

# A ContextVar is like a thread-local, but correct for asyncio: each request (task) sees its own value.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

STANDARD_ATTRS = set(logging.LogRecord("x", 0, "x", 0, "x", None, None).__dict__) | {"message", "asctime"}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line: what Datadog / Loki / CloudWatch / ELK expect."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_var.get()),
        }
        payload.update({k: v for k, v in record.__dict__.items() if k not in STANDARD_ATTRS and k != "request_id"})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("app")
    logger.setLevel(level)
    if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
        logger.addFilter(RequestIdFilter())
        for child in ("app.access", "app.orders"):
            logging.getLogger(child).addFilter(RequestIdFilter())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger
