"""Minimal mod scanner tests (issue #19, walking-skeleton scope)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rimtrans.errors import FatalError
from rimtrans.scanner import scan_mod

FIXTURE_MOD = Path(__file__).parent / "fixtures" / "skeleton_mod"


def _write_about(mod_dir: Path, body: str) -> None:
    about_dir = mod_dir / "About"
    about_dir.mkdir(parents=True, exist_ok=True)
    (about_dir / "About.xml").write_text(body, encoding="utf-8")


def test_scans_root_level_languages_folder() -> None:
    mod = scan_mod(FIXTURE_MOD)

    assert mod.mod_id == "test.skeletonmod"
    assert mod.name == "Skeleton Test Mod"
    assert mod.supported_versions == ("1.6",)
    assert mod.content_root == FIXTURE_MOD
    assert (mod.content_root / "Languages").is_dir()


def test_resolves_version_scoped_languages_folder(tmp_path: Path) -> None:
    mod_dir = tmp_path / "VersionScopedMod"
    _write_about(
        mod_dir,
        "<ModMetaData><name>V</name><packageId>test.v</packageId></ModMetaData>",
    )
    (mod_dir / "1.6" / "Languages" / "English" / "Keyed").mkdir(parents=True)

    mod = scan_mod(mod_dir)

    assert mod.content_root == mod_dir / "1.6"


def test_missing_mod_directory_raises_fatal_error(tmp_path: Path) -> None:
    with pytest.raises(FatalError, match="not a directory"):
        scan_mod(tmp_path / "does-not-exist")


def test_missing_about_xml_raises_fatal_error(tmp_path: Path) -> None:
    mod_dir = tmp_path / "NoAbout"
    mod_dir.mkdir()

    with pytest.raises(FatalError, match="About/About.xml"):
        scan_mod(mod_dir)


def test_malformed_about_xml_raises_fatal_error(tmp_path: Path) -> None:
    mod_dir = tmp_path / "BadXml"
    _write_about(mod_dir, "<ModMetaData><name>Oops</ModMetaData>")

    with pytest.raises(FatalError, match="Malformed About.xml"):
        scan_mod(mod_dir)


def test_missing_package_id_raises_fatal_error(tmp_path: Path) -> None:
    mod_dir = tmp_path / "NoPackageId"
    _write_about(mod_dir, "<ModMetaData><name>NoId</name></ModMetaData>")

    with pytest.raises(FatalError, match="packageId"):
        scan_mod(mod_dir)


def test_no_languages_folder_raises_fatal_error(tmp_path: Path) -> None:
    mod_dir = tmp_path / "NoLanguages"
    _write_about(
        mod_dir,
        "<ModMetaData><name>N</name><packageId>test.n</packageId></ModMetaData>",
    )

    with pytest.raises(FatalError, match="Languages"):
        scan_mod(mod_dir)
