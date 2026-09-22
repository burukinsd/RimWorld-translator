"""End-to-end walking-skeleton pipeline test (issue #73): fixture mod ->
scan -> extract -> translate -> validate -> generate -> structural
validation of the generated output tree."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import pytest

from rimtrans.errors import FatalError
from rimtrans.pipeline import run_build, run_translate

FIXTURE_MOD = Path(__file__).parent / "fixtures" / "skeleton_mod"


def test_translate_then_build_produces_loadable_output_tree(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    translate_result = run_translate(FIXTURE_MOD, output_dir)
    assert translate_result.mod.mod_id == "test.skeletonmod"
    assert translate_result.passed_count == len(translate_result.results) == 3

    build_result = run_build(output_dir)

    assert build_result.emitted_count == 3
    assert build_result.keyed_path.is_file()
    assert build_result.about_path.is_file()

    keyed_root = ElementTree.fromstring(build_result.keyed_path.read_bytes())
    keys = {child.tag: child.text for child in keyed_root}
    assert keys == {
        "JumpToLocation": "[RU] Jump to location",
        "PawnArrived": "[RU] {PAWN_nameDef} has arrived.",
        "RecruitSuccess": "[RU] {0} successfully recruited {1} ({2} chance).",
    }

    about_root = ElementTree.fromstring(build_result.about_path.read_bytes())
    load_after_li = about_root.find("loadAfter/li")
    assert load_after_li is not None
    assert load_after_li.text == "test.skeletonmod"

    # The generated mod must live entirely under the output directory —
    # the source fixture mod is never written to.
    assert build_result.output_mod_dir.is_relative_to(output_dir)


def test_build_without_prior_translate_raises_fatal_error(tmp_path: Path) -> None:
    with pytest.raises(FatalError, match="run 'rimtrans translate' first"):
        run_build(tmp_path / "output")
