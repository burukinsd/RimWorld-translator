"""CLI smoke tests (issue #16): --help lists every planned command, and
each stub command exits cleanly with a clear "not implemented" message."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from rimtrans.cli.main import _OWNING_EPIC, app

runner = CliRunner()

EXPECTED_COMMANDS = [
    "scan",
    "diff",
    "translate",
    "validate",
    "build",
    "report",
    "glossary",
    "benchmark",
]


def test_help_lists_all_planned_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in EXPECTED_COMMANDS:
        assert command in result.output


def test_all_expected_commands_have_an_owning_epic() -> None:
    assert set(_OWNING_EPIC) == set(EXPECTED_COMMANDS)


def test_each_stub_command_exits_cleanly_with_not_implemented_message() -> None:
    for command in EXPECTED_COMMANDS:
        result = runner.invoke(app, [command])

        assert result.exit_code == 0, f"{command} exited {result.exit_code}: {result.output}"
        assert "not yet implemented" in result.output
        epic_number, _ = _OWNING_EPIC[command]
        assert f"Epic #{epic_number}" in result.output


def test_config_flag_with_valid_config_is_accepted() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    example_config = repo_root / "config" / "example.yaml"

    result = runner.invoke(app, ["--config", str(example_config), "scan"])

    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_config_flag_with_missing_file_fails_with_clear_error() -> None:
    result = runner.invoke(app, ["--config", "does-not-exist.yaml", "scan"])

    assert result.exit_code == 1
    assert "Config file not found" in result.output
