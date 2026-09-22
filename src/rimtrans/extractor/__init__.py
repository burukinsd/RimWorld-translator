"""DefInjected/Keyed/Strings extraction.

Full scope (DefInjected, Strings, Def-field tables) is Epic #2. This
module implements only the walking skeleton's minimal slice (issue #71/
#73/#21): `Keyed/` extraction, per `RIMWORLD_LOCALIZATION.md` §3.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from rimtrans.batch import run_batch
from rimtrans.core.models import Domain, SourceString
from rimtrans.errors import RecoverableError
from rimtrans.log import get_logger

_logger = get_logger("extractor")


def _parse_keyed_file(path: Path) -> dict[str, str]:
    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError as exc:
        raise RecoverableError(f"Malformed Keyed XML at {path}: {exc}") from exc

    entries: dict[str, str] = {}
    for child in root:
        if not isinstance(child.tag, str):
            continue  # skip comments/PIs interspersed among elements
        entries[child.tag] = child.text or ""
    return entries


def extract_keyed(
    mod_id: str, content_root: Path, *, language: str = "English"
) -> list[SourceString]:
    """Extract `SourceString`s from `<content_root>/Languages/<language>/Keyed/`.

    Every `Keyed/*.xml` file is merged into one flat key space, per
    `RIMWORLD_LOCALIZATION.md` §3 ("filename is arbitrary to the engine").
    A malformed individual file is skipped (logged, not fatal) via
    `run_batch`; a duplicate key across files keeps the first value seen
    and logs a warning, since load-order-aware override semantics are a
    generation-time concern (Epic #8) out of scope here.
    """
    keyed_dir = content_root / "Languages" / language / "Keyed"
    if not keyed_dir.is_dir():
        return []

    files = sorted(keyed_dir.glob("*.xml"))
    batch_result = run_batch(files, _parse_keyed_file, logger=_logger)

    merged: dict[str, str] = {}
    for file_entries in batch_result.successes:
        for key, value in file_entries.items():
            if key in merged:
                _logger.warning("duplicate Keyed key %r across files, keeping first value", key)
                continue
            merged[key] = value

    return [
        SourceString(
            mod_id=mod_id,
            domain=Domain.KEYED,
            key_path=key,
            source_text=value,
        )
        for key, value in merged.items()
    ]
