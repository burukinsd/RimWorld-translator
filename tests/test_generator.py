"""Keyed tree / About.xml generator tests (issue #52/#53, walking-skeleton scope)."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from rimtrans.core.models import Domain, SourceString, TranslationResult, ValidationStatus
from rimtrans.generator import generate_about_xml, generate_keyed_tree
from rimtrans.scanner import ModInfo


def _result(key: str, source: str, translated: str, status: ValidationStatus) -> TranslationResult:
    return TranslationResult(
        source=SourceString(mod_id="mod", domain=Domain.KEYED, key_path=key, source_text=source),
        translated_text=translated,
        provider_id="p",
        prompt_version="v1",
        validation_status=status,
    )


def test_generate_keyed_tree_writes_only_passed_entries(tmp_path: Path) -> None:
    results = [
        _result("A", "hello", "[RU] hello", ValidationStatus.PASSED),
        _result("B", "world", "[RU] world", ValidationStatus.FAILED),
        _result("C", "again", "[RU] again", ValidationStatus.PENDING),
    ]

    out_path = generate_keyed_tree(tmp_path, "mod", results)

    assert out_path == tmp_path / "Languages" / "Russian" / "Keyed" / "mod.xml"
    root = ElementTree.fromstring(out_path.read_bytes())
    tags = [child.tag for child in root]
    assert tags == ["A"]
    entry = root.find("A")
    assert entry is not None
    assert entry.text == "[RU] hello"


def test_generate_keyed_tree_includes_en_comment(tmp_path: Path) -> None:
    results = [_result("A", "hello world", "[RU] hello world", ValidationStatus.PASSED)]

    out_path = generate_keyed_tree(tmp_path, "mod", results)

    content = out_path.read_text(encoding="utf-8")
    assert "<!-- EN: hello world -->" in content


def test_generate_keyed_tree_is_deterministic_and_sorted(tmp_path: Path) -> None:
    results = [
        _result("Zeta", "z", "[RU] z", ValidationStatus.PASSED),
        _result("Alpha", "a", "[RU] a", ValidationStatus.PASSED),
    ]

    first = generate_keyed_tree(tmp_path / "run1", "mod", results)
    second = generate_keyed_tree(tmp_path / "run2", "mod", results)

    assert first.read_bytes() == second.read_bytes()
    root = ElementTree.fromstring(first.read_bytes())
    assert [child.tag for child in root] == ["Alpha", "Zeta"]


def test_generate_keyed_tree_handles_no_passed_entries(tmp_path: Path) -> None:
    results = [_result("A", "hello", "[RU] hello", ValidationStatus.FAILED)]

    out_path = generate_keyed_tree(tmp_path, "mod", results)

    root = ElementTree.fromstring(out_path.read_bytes())
    assert list(root) == []


def _mod(mod_id: str, name: str) -> ModInfo:
    return ModInfo(
        mod_id=mod_id, name=name, supported_versions=("1.6",), content_root=Path("/tmp/x")
    )


def test_generate_about_xml_lists_translated_mods(tmp_path: Path) -> None:
    mods = [_mod("author.mod", "Some Mod")]

    out_path = generate_about_xml(tmp_path, mods)

    root = ElementTree.fromstring(out_path.read_bytes())
    package_id_el = root.find("packageId")
    assert package_id_el is not None and package_id_el.text
    load_after = [li.text for li in root.findall("loadAfter/li")]
    assert load_after == ["author.mod"]
    dep_package_ids = [dep.find("packageId") for dep in root.findall("modDependencies/li")]
    assert [el.text if el is not None else None for el in dep_package_ids] == ["author.mod"]


def test_generate_about_xml_is_byte_identical_across_runs(tmp_path: Path) -> None:
    mods = [_mod("author.mod", "Some Mod"), _mod("author.other", "Other Mod")]

    first = generate_about_xml(tmp_path / "run1", mods)
    second = generate_about_xml(tmp_path / "run2", mods)

    assert first.read_bytes() == second.read_bytes()


def test_generate_about_xml_with_no_mods_omits_dependency_sections(tmp_path: Path) -> None:
    out_path = generate_about_xml(tmp_path, [])

    root = ElementTree.fromstring(out_path.read_bytes())
    assert root.find("modDependencies") is None
    assert root.find("loadAfter") is None
