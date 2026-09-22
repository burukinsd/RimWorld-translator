"""Config loading and validation.

Turns YAML-parse errors and Pydantic `ValidationError`s into a single
`ConfigError` with a specific, actionable message — never a bare parser
traceback — per issue #14's acceptance criteria.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from rimtrans.config.schema import RimTransConfig
from rimtrans.errors import ConfigError


def _format_validation_error(exc: ValidationError) -> str:
    lines = [f"Config validation failed with {exc.error_count()} error(s):"]
    for error in exc.errors():
        field_path = ".".join(str(part) for part in error["loc"]) or "<root>"
        lines.append(f"  - {field_path}: {error['msg']}")
    return "\n".join(lines)


def load_config(path: Path) -> RimTransConfig:
    """Load and validate a rimtrans config file.

    Raises `ConfigError` (a `FatalError`) with a message identifying
    exactly what's wrong — missing file, invalid YAML, or a specific
    field failing schema validation.
    """
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    if not path.is_file():
        raise ConfigError(f"Config path is not a file: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Config file is not valid YAML: {path}\n{exc}") from exc

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError(
            f"Config file must contain a mapping at the top level, got {type(raw).__name__}: {path}"
        )

    try:
        return RimTransConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"{_format_validation_error(exc)}\n(in {path})") from exc
