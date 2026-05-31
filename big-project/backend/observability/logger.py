"""
AI创作工坊 - Structured JSON Logging

Provides structured logging with correlation IDs and request context.
Uses structlog for JSON-formatted, machine-readable log output.
"""

import logging
import sys
from typing import Any

import structlog

_configured = False


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured JSON logging with structlog.

    Sets up:
    - JSON renderer for production
    - Console renderer for development
    - Correlation ID processor
    - Timestamp and log level processors
    """
    global _configured
    if _configured:
        return

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set root logger level
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    _configured = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog BoundLogger

    Usage:
        logger = get_logger(__name__)
        logger.info("Request processed", user_id="123", duration_ms=42)
    """
    if not _configured:
        setup_logging()
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables to the current logging context.

    These will appear in all subsequent log entries in this context.

    Args:
        **kwargs: Key-value pairs to bind

    Usage:
        bind_context(correlation_id="abc-123", user_id="456")
        logger.info("Processing request")  # includes correlation_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """Remove context variables from the current logging context."""
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()
