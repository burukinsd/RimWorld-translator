"""Shared error hierarchy used across every component.

Two kinds of failure exist in this pipeline, and every component that can
fail must pick one deliberately (see `docs/adr/0002-logging-and-error-
conventions.md`):

- `RecoverableError` — a per-item failure (one malformed XML file, one
  provider call, one validation failure). The surrounding batch/pipeline
  must record it and continue with the remaining items.
- `FatalError` — a run-level failure (missing/malformed config, a
  provider that can't be reached at all). The current command must abort.
"""

from __future__ import annotations


class RimTransError(Exception):
    """Base class for all rimtrans errors."""


class FatalError(RimTransError):
    """A run-level error. The current command should abort."""


class RecoverableError(RimTransError):
    """A per-item error. The pipeline should record it and continue."""


class ConfigError(FatalError):
    """The config file is missing, malformed, or fails schema validation."""
