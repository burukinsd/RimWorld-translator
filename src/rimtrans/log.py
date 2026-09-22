"""Logging setup and conventions.

Console output stays human-readable; an optional per-run log file is
written as structured JSON lines so `rimtrans report` (Epic #9) and ad hoc
log filtering can key on `mod_id` / `domain` / `key` / `provider` without
parsing free text.

Convention for callers: use `get_logger(component, **context)` to attach
structured fields once (e.g. `mod_id`), then log normally — the fields ride
along on every message from that logger.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

ROOT_LOGGER_NAME = "rimtrans"

# Fields promoted to top-level keys in the structured (file) log output when
# present on a record. Any component may pass these via `extra=` or via
# `get_logger(..., **context)`.
STRUCTURED_FIELDS = ("mod_id", "domain", "key", "provider")


class StructuredFormatter(logging.Formatter):
    """Renders a log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(verbose: bool = False, log_file: Path | None = None) -> None:
    """Configure the `rimtrans` logger tree.

    Idempotent: safe to call more than once (e.g. once per CLI invocation)
    without accumulating duplicate handlers.
    """
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(level)
    root.handlers.clear()
    root.propagate = False

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
    root.addHandler(console)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(StructuredFormatter())
        root.addHandler(file_handler)


def get_logger(component: str, **context: object) -> logging.LoggerAdapter:
    """Return a logger for `component`, pre-tagged with structured `context`.

    Example: `get_logger("extractor", mod_id="RimHUD", domain="Keyed")`.
    """
    logger = logging.getLogger(f"{ROOT_LOGGER_NAME}.{component}")
    return logging.LoggerAdapter(logger, extra=context)
