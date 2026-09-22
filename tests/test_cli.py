"""CLI smoke tests (issue #16): --help lists every planned command, and
each stub command exits cleanly with a clear "not implemented" message.

`translate`/`build` are implemented at walking-skeleton scope (issue #73)
and are no longer stubs — see `test_each_stub_command_exits_cleanly_...`
below for the remaining stubs, and `test_translate_then_build_*` for the
implemented pair.
"""

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

STUB_COMMANDS = [c for c in EXPECTED_COMMANDS if c not in ("translate", "build")]

FIXTURE_MOD = Path(__file__).parent / "fixtures" / "skeleton_mod"


def test_help_lists_all_planned_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in EXPECTED_COMMANDS:
        assert command in result.output


def test_all_stub_commands_have_an_owning_epic() -> None:
    assert set(_OWNING_EPIC) == set(STUB_COMMANDS)


def test_each_stub_command_exits_cleanly_with_not_implemented_message() -> None:
    for command in STUB_COMMANDS:
        result = runner.invoke(app, [command])

        assert result.exit_code == 0, f"{command} exited {result.exit_code}: {result.output}"
        assert "not yet implemented" in result.output
        epic_number, _ = _OWNING_EPIC[command]
        assert f"Epic #{epic_number}" in result.output


def test_translate_then_build_via_cli_produce_output_tree(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    translate_result = runner.invoke(
        app, ["translate", "--mod-path", str(FIXTURE_MOD), "-o", str(output_dir)]
    )
    assert translate_result.exit_code == 0, translate_result.output
    assert "Translated 3 Keyed string(s)" in translate_result.output

    build_result = runner.invoke(app, ["build", "-o", str(output_dir)])
    assert build_result.exit_code == 0, build_result.output
    assert "Generated" in build_result.output

    output_mod_dir = output_dir / "RimTransWalkingSkeletonRU"
    keyed_path = output_mod_dir / "Languages" / "Russian" / "Keyed" / "test.skeletonmod.xml"
    about_path = output_mod_dir / "About" / "About.xml"
    assert keyed_path.is_file()
    assert about_path.is_file()


def test_build_before_translate_fails_with_clear_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["build", "-o", str(tmp_path / "output")])

    assert result.exit_code == 1
    assert "rimtrans translate" in result.output


def test_translate_with_missing_mod_path_fails_with_clear_error(tmp_path: Path) -> None:
    missing_mod = tmp_path / "no-such-mod"
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app, ["translate", "--mod-path", str(missing_mod), "-o", str(output_dir)]
    )

    assert result.exit_code != 0


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
