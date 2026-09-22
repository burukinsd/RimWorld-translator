"""Wire scan -> extract -> translate -> validate -> generate (issue #73).

Pure integration over already-scoped-down walking-skeleton pieces — no new
extraction/validation/generation logic lives here. There is no Translation
Memory yet (Epic #3): `run_translate` persists its draft results to a JSON
state file that `run_build` reads back, which is an acceptable stateless
stand-in for this milestone only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from rimtrans.core.models import (
    Domain,
    GlossaryRules,
    ReviewStatus,
    SemanticContext,
    SourceString,
    TranslationResult,
    ValidationStatus,
)
from rimtrans.errors import FatalError
from rimtrans.extractor import extract_keyed
from rimtrans.generator import generate_about_xml, generate_keyed_tree
from rimtrans.log import get_logger
from rimtrans.providers.passthrough import PassthroughProvider
from rimtrans.scanner import ModInfo, scan_mod
from rimtrans.validator import validate

_logger = get_logger("pipeline")

STATE_FILENAME = "walking_skeleton_state.json"
OUTPUT_MOD_DIR_NAME = "RimTransWalkingSkeletonRU"


def _state_path(output_dir: Path) -> Path:
    return output_dir / STATE_FILENAME


def _result_to_dict(result: TranslationResult) -> dict[str, Any]:
    source = result.source
    return {
        "mod_id": source.mod_id,
        "domain": source.domain.value,
        "key_path": source.key_path,
        "source_text": source.source_text,
        "def_type": source.def_type,
        "semantic_type": source.semantic_type,
        "translated_text": result.translated_text,
        "provider_id": result.provider_id,
        "prompt_version": result.prompt_version,
        "validation_status": result.validation_status.value,
        "review_status": result.review_status.value,
    }


def _result_from_dict(d: dict[str, Any]) -> TranslationResult:
    source = SourceString(
        mod_id=d["mod_id"],
        domain=Domain(d["domain"]),
        key_path=d["key_path"],
        source_text=d["source_text"],
        def_type=d.get("def_type"),
        semantic_type=d.get("semantic_type"),
    )
    return TranslationResult(
        source=source,
        translated_text=d["translated_text"],
        provider_id=d["provider_id"],
        prompt_version=d["prompt_version"],
        validation_status=ValidationStatus(d["validation_status"]),
        review_status=ReviewStatus(d["review_status"]),
    )


def _mod_to_dict(mod: ModInfo) -> dict[str, Any]:
    return {
        "mod_id": mod.mod_id,
        "name": mod.name,
        "supported_versions": list(mod.supported_versions),
        "content_root": str(mod.content_root),
    }


def _mod_from_dict(d: dict[str, Any]) -> ModInfo:
    return ModInfo(
        mod_id=d["mod_id"],
        name=d["name"],
        supported_versions=tuple(d["supported_versions"]),
        content_root=Path(d["content_root"]),
    )


@dataclass(frozen=True, slots=True)
class TranslateRunResult:
    mod: ModInfo
    results: list[TranslationResult]

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.validation_status == ValidationStatus.PASSED)


def run_translate(mod_path: Path, output_dir: Path) -> TranslateRunResult:
    """Scan `mod_path`, extract its Keyed strings, translate, validate, persist state."""
    mod = scan_mod(mod_path)
    source_strings = extract_keyed(mod.mod_id, mod.content_root)

    provider = PassthroughProvider()
    raw_results = provider.translate(source_strings, SemanticContext(), GlossaryRules())

    validated: list[TranslationResult] = []
    for result in raw_results:
        outcome = validate(result.source, result)
        status = ValidationStatus.PASSED if outcome.passed else ValidationStatus.FAILED
        if not outcome.passed:
            _logger.warning(
                "validation failed for %s: %s",
                result.source.key_path,
                "; ".join(outcome.failures),
            )
        validated.append(replace(result, validation_status=status))

    output_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "schema_version": 1,
        "mod": _mod_to_dict(mod),
        "results": [_result_to_dict(r) for r in validated],
    }
    _state_path(output_dir).write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return TranslateRunResult(mod=mod, results=validated)


@dataclass(frozen=True, slots=True)
class BuildRunResult:
    output_mod_dir: Path
    keyed_path: Path
    about_path: Path
    emitted_count: int


def run_build(output_dir: Path) -> BuildRunResult:
    """Generate the standalone translation mod from `run_translate`'s persisted state."""
    state_path = _state_path(output_dir)
    if not state_path.is_file():
        raise FatalError(
            f"No translation state found at {state_path} — run 'rimtrans translate' first."
        )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    mod = _mod_from_dict(state["mod"])
    results = [_result_from_dict(d) for d in state["results"]]

    output_mod_dir = output_dir / OUTPUT_MOD_DIR_NAME
    keyed_path = generate_keyed_tree(output_mod_dir, mod.mod_id, results)
    about_path = generate_about_xml(output_mod_dir, [mod])

    emitted_count = sum(1 for r in results if r.validation_status == ValidationStatus.PASSED)
    return BuildRunResult(
        output_mod_dir=output_mod_dir,
        keyed_path=keyed_path,
        about_path=about_path,
        emitted_count=emitted_count,
    )
