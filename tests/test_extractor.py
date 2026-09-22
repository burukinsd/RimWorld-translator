"""Keyed extractor tests (issue #21, walking-skeleton scope)."""

from __future__ import annotations

from pathlib import Path

from rimtrans.core.models import Domain
from rimtrans.extractor import extract_keyed

FIXTURE_MOD = Path(__file__).parent / "fixtures" / "skeleton_mod"


def test_extracts_all_keyed_entries_from_fixture_mod() -> None:
    strings = extract_keyed("test.skeletonmod", FIXTURE_MOD)

    by_key = {s.key_path: s for s in strings}
    assert set(by_key) == {"JumpToLocation", "RecruitSuccess", "PawnArrived"}
    assert all(s.domain == Domain.KEYED for s in strings)
    assert all(s.mod_id == "test.skeletonmod" for s in strings)
    assert by_key["JumpToLocation"].source_text == "Jump to location"


def test_preserves_positional_and_named_tokens_byte_for_byte() -> None:
    strings = extract_keyed("test.skeletonmod", FIXTURE_MOD)
    by_key = {s.key_path: s for s in strings}

    assert by_key["RecruitSuccess"].source_text == "{0} successfully recruited {1} ({2} chance)."
    assert by_key["PawnArrived"].source_text == "{PAWN_nameDef} has arrived."


def test_merges_multiple_keyed_files(tmp_path: Path) -> None:
    keyed_dir = tmp_path / "Languages" / "English" / "Keyed"
    keyed_dir.mkdir(parents=True)
    (keyed_dir / "A.xml").write_text(
        "<LanguageData><KeyA>value a</KeyA></LanguageData>", encoding="utf-8"
    )
    (keyed_dir / "B.xml").write_text(
        "<LanguageData><KeyB>value b</KeyB></LanguageData>", encoding="utf-8"
    )

    strings = extract_keyed("mod", tmp_path)

    assert {s.key_path: s.source_text for s in strings} == {
        "KeyA": "value a",
        "KeyB": "value b",
    }


def test_duplicate_key_across_files_keeps_first_value(tmp_path: Path) -> None:
    keyed_dir = tmp_path / "Languages" / "English" / "Keyed"
    keyed_dir.mkdir(parents=True)
    (keyed_dir / "A.xml").write_text(
        "<LanguageData><Dup>first</Dup></LanguageData>", encoding="utf-8"
    )
    (keyed_dir / "B.xml").write_text(
        "<LanguageData><Dup>second</Dup></LanguageData>", encoding="utf-8"
    )

    strings = extract_keyed("mod", tmp_path)

    assert len(strings) == 1
    assert strings[0].source_text == "first"


def test_malformed_file_is_skipped_not_fatal(tmp_path: Path) -> None:
    keyed_dir = tmp_path / "Languages" / "English" / "Keyed"
    keyed_dir.mkdir(parents=True)
    (keyed_dir / "Bad.xml").write_text("<LanguageData><Oops></LanguageData>", encoding="utf-8")
    (keyed_dir / "Good.xml").write_text(
        "<LanguageData><Fine>ok</Fine></LanguageData>", encoding="utf-8"
    )

    strings = extract_keyed("mod", tmp_path)

    assert len(strings) == 1
    assert strings[0].key_path == "Fine"


def test_no_keyed_folder_returns_empty_list(tmp_path: Path) -> None:
    assert extract_keyed("mod", tmp_path) == []
