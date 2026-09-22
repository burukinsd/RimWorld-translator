"""Config loading: valid configs load; invalid ones fail with a specific,
actionable message rather than a generic parse error (issue #14)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rimtrans.config.loader import load_config
from rimtrans.errors import ConfigError

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_CONFIG = REPO_ROOT / "config" / "example.yaml"

VALID_MINIMAL = """
translation_memory:
  path: ./data/tm.sqlite3
providers:
  - id: local:ollama:test-model
    kind: local
    model: test-model
"""


def test_example_config_loads_successfully() -> None:
    config = load_config(EXAMPLE_CONFIG)

    assert str(config.translation_memory.path) == "data/translation_memory.sqlite3"
    assert len(config.providers) == 2
    assert config.providers[0].kind.value == "local"
    assert config.providers[1].kind.value == "remote"
    assert config.router_policy.always_escalate_semantic_types == ["quest_text"]
    assert len(config.semantic_type_overrides) == 2


def test_minimal_valid_config_loads(tmp_path: Path) -> None:
    config_path = tmp_path / "rimtrans.yaml"
    config_path.write_text(VALID_MINIMAL, encoding="utf-8")

    config = load_config(config_path)

    assert config.providers[0].id == "local:ollama:test-model"
    # Defaults are applied.
    assert config.router_policy.max_local_retries == 2
    assert config.glossary.sources == []


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "does-not-exist.yaml")


def test_missing_required_field_raises_actionable_error(tmp_path: Path) -> None:
    config_path = tmp_path / "rimtrans.yaml"
    config_path.write_text("providers: []\n", encoding="utf-8")

    with pytest.raises(ConfigError) as excinfo:
        load_config(config_path)

    message = str(excinfo.value)
    assert "translation_memory" in message
    # Empty providers list should also be flagged (min_length=1).
    assert "providers" in message


def test_malformed_provider_kind_raises_actionable_error(tmp_path: Path) -> None:
    config_path = tmp_path / "rimtrans.yaml"
    config_path.write_text(
        """
translation_memory:
  path: ./tm.sqlite3
providers:
  - id: bad-provider
    kind: cloud
    model: x
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        load_config(config_path)

    message = str(excinfo.value)
    assert "providers.0.kind" in message


def test_malformed_yaml_raises_config_error(tmp_path: Path) -> None:
    config_path = tmp_path / "rimtrans.yaml"
    config_path.write_text("translation_memory: [unclosed\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="not valid YAML"):
        load_config(config_path)


def test_duplicate_provider_ids_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "rimtrans.yaml"
    config_path.write_text(
        """
translation_memory:
  path: ./tm.sqlite3
providers:
  - id: dup
    kind: local
    model: x
  - id: dup
    kind: remote
    model: y
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="duplicate provider id"):
        load_config(config_path)


def test_unknown_field_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "rimtrans.yaml"
    config_path.write_text(
        """
translation_memory:
  path: ./tm.sqlite3
providers:
  - id: p
    kind: local
    model: x
unknown_field: 1
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="unknown_field"):
        load_config(config_path)
