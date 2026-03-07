"""
Request tracing utilities for PII-safe logging.

This module provides trace ID management to avoid logging personally
identifiable information (PII) such as usernames, emails, etc.
"""

import uuid
from contextvars import ContextVar
from typing import Optional
import logging

# Context variable to store trace ID for the current request
_trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def generate_trace_id() -> str:
    """Generate a unique trace ID for request tracking"""
    return str(uuid.uuid4())


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current context"""
    _trace_id_context.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get the trace ID from the current context"""
    return _trace_id_context.get()


def clear_trace_id() -> None:
    """Clear the trace ID from the current context"""
    _trace_id_context.set(None)


class TraceIDFilter(logging.Filter):
    """
    Logging filter that adds trace_id to all log records.

    This allows trace IDs to be included in log formatting without
    manually passing them to each log call.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace_id to the log record"""
        record.trace_id = get_trace_id() or "no-trace"
        return True


def setup_trace_logging():
    """
    Configure logging to include trace IDs in all log messages.

    Call this during application startup to enable trace ID logging.
    """
    # Add the trace ID filter to the root logger
    root_logger = logging.getLogger()
    root_logger.addFilter(TraceIDFilter())

    # Update the logging format to include trace_id
    for handler in root_logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - [%(trace_id)s] - %(name)s - " "%(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
