"""Structured JSON logging with secret redaction."""

from __future__ import annotations

import logging
import re

import structlog

_SENSITIVE_KEYS = re.compile(r"pass(word)?|secret|token|otp|code_hash|authorization|signature|card|cvv", re.I)


def _redact(_logger, _method, event_dict: dict) -> dict:
    for key in list(event_dict):
        if key != "event" and _SENSITIVE_KEYS.search(key):
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging(level: str = "INFO", json: bool = True) -> None:
    logging.basicConfig(format="%(message)s", level=level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact,
            structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
