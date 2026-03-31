"""Structured logging infrastructure with request context propagation.

Uses contextvars to propagate request_id, user_id, and path across
the entire request lifecycle without passing them explicitly through
every function call.

Usage:
    # In middleware (automatic):
    set_request_context(request_id, user_id=..., path=request.path)

    # In any module:
    from common.logging import get_context_extra
    logger.info("Processing query", extra=get_context_extra())
"""

from __future__ import annotations

import contextvars
import logging
from typing import Any

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
_user_id: contextvars.ContextVar[int | None] = contextvars.ContextVar("user_id", default=None)
_request_path: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_path", default=None)


def set_request_context(
    request_id: str,
    user_id: int | None = None,
    path: str | None = None,
) -> None:
    """Set request context for the current async/thread context."""
    _request_id.set(request_id)
    _user_id.set(user_id)
    _request_path.set(path)


def clear_request_context() -> None:
    """Clear request context after response is sent."""
    _request_id.set(None)
    _user_id.set(None)
    _request_path.set(None)


def get_context_extra() -> dict[str, Any]:
    """Get current request context as a dict suitable for logger extra={}."""
    return {
        "request_id": _request_id.get(),
        "user_id": _user_id.get(),
        "path": _request_path.get(),
    }


class ContextFilter(logging.Filter):
    """Logging filter that injects request context into every log record.

    This allows the formatter to include {request_id} without every
    logging call needing to pass extra={}.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get() or "-"  # type: ignore[attr-defined]
        record.user_id = _user_id.get()  # type: ignore[attr-defined]
        record.path = _request_path.get()  # type: ignore[attr-defined]
        return True
