"""Mod discovery and version resolution.

Full scope — Workshop discovery, `LoadFolders.xml`-aware resolution — is
Epic #2 (issue #19). This module implements only the walking skeleton's
minimal slice (issue #71/#73): scan a single, explicitly given local mod
directory and resolve its RimWorld-1.6 content root, either at the mod
root or under a version-scoped subfolder (`RIMWORLD_LOCALIZATION.md` §1).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from rimtrans.errors import FatalError

DEFAULT_GAME_VERSION = "1.6"


@dataclass(frozen=True, slots=True)
class ModInfo:
    """A scanned mod's identity and resolved RimWorld-1.6 content root."""

    mod_id: str
    name: str
    supported_versions: tuple[str, ...]
    content_root: Path
    """Directory that directly contains `Languages/` for this mod/version."""


def _resolve_content_root(mod_path: Path, game_version: str) -> Path:
    version_scoped = mod_path / game_version
    if (version_scoped / "Languages").is_dir():
        return version_scoped
    if (mod_path / "Languages").is_dir():
        return mod_path
    raise FatalError(
        f"Mod at {mod_path} has no 'Languages/' folder at its root or under "
        f"'{game_version}/' — cannot resolve a content root."
    )


def scan_mod(mod_path: Path, *, game_version: str = DEFAULT_GAME_VERSION) -> ModInfo:
    """Scan one local mod directory and resolve its RimWorld-`game_version` content root.

    Raises `FatalError` if `mod_path` doesn't exist, its `About/About.xml`
    is missing/malformed, or no `Languages/` folder can be resolved for
    `game_version`.
    """
    if not mod_path.is_dir():
        raise FatalError(f"Mod path is not a directory: {mod_path}")

    about_path = mod_path / "About" / "About.xml"
    if not about_path.is_file():
        raise FatalError(f"Mod at {mod_path} has no 'About/About.xml'.")

    try:
        root = ElementTree.parse(about_path).getroot()
    except ElementTree.ParseError as exc:
        raise FatalError(f"Malformed About.xml at {about_path}: {exc}") from exc

    package_id_el = root.find("packageId")
    name_el = root.find("name")
    package_id = ((package_id_el.text or "") if package_id_el is not None else "").strip()
    name = ((name_el.text or "") if name_el is not None else "").strip()
    if not package_id:
        raise FatalError(f"About.xml at {about_path} is missing a <packageId>.")
    if not name:
        raise FatalError(f"About.xml at {about_path} is missing a <name>.")

    supported_versions = tuple(
        (li.text or "").strip()
        for li in root.findall("supportedVersions/li")
        if (li.text or "").strip()
    )

    content_root = _resolve_content_root(mod_path, game_version)

    return ModInfo(
        mod_id=package_id,
        name=name,
        supported_versions=supported_versions,
        content_root=content_root,
    )
