"""Structured logging with a per-request correlation ID."""
import json  # noqa: F401
import logging
from contextvars import ContextVar
from datetime import datetime, timezone  # noqa: F401

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# The attributes every LogRecord has; anything else came from `extra={...}`.
STANDARD_ATTRS = set(logging.LogRecord("x", 0, "x", 0, "x", None, None).__dict__) | {"message", "asctime"}


class RequestIdFilter(logging.Filter):
    """TODO: set record.request_id = request_id_var.get() and return True."""


class JsonFormatter(logging.Formatter):
    """TODO: format() returns ONE JSON line with keys
    ts (ISO-8601 UTC), level, logger, message, request_id, plus every `extra` field
    (attributes not in STANDARD_ATTRS), plus "exception" (formatted traceback) when record.exc_info is set."""


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """TODO: get the "app" logger, set the level, add a RequestIdFilter to "app", "app.access" and "app.orders"
    (only once!), and a StreamHandler with JsonFormatter (only once). Return the "app" logger."""
    return logging.getLogger("app")
