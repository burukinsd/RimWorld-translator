"""Deterministic translation-mod builder.

Full scope (DefInjected/Strings writers, multi-mod output namespacing) is
Epic #8. This module implements only the walking skeleton's minimal slice
(issue #71/#73/#52/#53): a single mod's `Languages/Russian/Keyed/` tree
and a basic `About.xml`, per `RIMWORLD_LOCALIZATION.md` §3 and §6.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from xml.etree.ElementTree import Comment, Element, SubElement, indent, tostring

from rimtrans.core.models import TranslationResult, ValidationStatus
from rimtrans.scanner import ModInfo

DEFAULT_MOD_NAME = "RimTrans Walking Skeleton [RU]"
DEFAULT_AUTHOR = "rimtrans"
DEFAULT_PACKAGE_ID = "rimtrans.walkingskeleton.ru"


def _comment_text(source_text: str) -> str:
    # XML comments may not contain "--" or end in "-"; defensively neutralize.
    safe = source_text.replace("--", "––").rstrip("-")
    return f" EN: {safe} "


def _write_xml(root: Element, path: Path) -> None:
    indent(root, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    xml_bytes = tostring(root, encoding="utf-8", xml_declaration=True)
    path.write_bytes(xml_bytes + b"\n")


def generate_keyed_tree(
    output_root: Path, mod_id: str, results: Sequence[TranslationResult]
) -> Path:
    """Write `<output_root>/Languages/Russian/Keyed/<mod_id>.xml`.

    Only `validation_status == PASSED` entries are ever emitted (issue #52
    acceptance criteria); the full scope's additional `review_status`
    gate has no meaning yet since no review pipeline exists in the
    walking skeleton. Entries are sorted by key for byte-identical,
    diffable output across re-runs.
    """
    accepted = sorted(
        (r for r in results if r.validation_status == ValidationStatus.PASSED),
        key=lambda r: r.source.key_path,
    )

    root = Element("LanguageData")
    for result in accepted:
        root.append(Comment(_comment_text(result.source.source_text)))
        entry = SubElement(root, result.source.key_path)
        entry.text = result.translated_text

    out_path = output_root / "Languages" / "Russian" / "Keyed" / f"{mod_id}.xml"
    _write_xml(root, out_path)
    return out_path


@dataclass(frozen=True, slots=True)
class AboutXmlOptions:
    """Overridable fields for the generated `About.xml`."""

    name: str = DEFAULT_MOD_NAME
    author: str = DEFAULT_AUTHOR
    package_id: str = DEFAULT_PACKAGE_ID
    game_version: str = "1.6"


_DEFAULT_ABOUT_OPTIONS = AboutXmlOptions()


def generate_about_xml(
    output_root: Path,
    translated_mods: Sequence[ModInfo],
    *,
    options: AboutXmlOptions = _DEFAULT_ABOUT_OPTIONS,
) -> Path:
    """Write `<output_root>/About/About.xml`.

    Deterministic: the same set of `translated_mods` always produces
    byte-identical output (issue #53 acceptance criteria) — mods are
    sorted by `mod_id` before emission.
    """
    mods = sorted(translated_mods, key=lambda m: m.mod_id)

    root = Element("ModMetaData")
    SubElement(root, "name").text = options.name
    SubElement(root, "author").text = options.author
    SubElement(root, "packageId").text = options.package_id
    description = ", ".join(m.name for m in mods) or "no source mods"
    SubElement(root, "description").text = f"Russian translation for: {description}."

    supported = SubElement(root, "supportedVersions")
    SubElement(supported, "li").text = options.game_version

    if mods:
        deps = SubElement(root, "modDependencies")
        for mod in mods:
            dep = SubElement(deps, "li")
            SubElement(dep, "packageId").text = mod.mod_id
            SubElement(dep, "displayName").text = mod.name

        load_after = SubElement(root, "loadAfter")
        for mod in mods:
            SubElement(load_after, "li").text = mod.mod_id

    out_path = output_root / "About" / "About.xml"
    _write_xml(root, out_path)
    return out_path
