"""Placeholder/tag/XML validation gates.

Full gate set (RulePack symbols, rich text, escapes, XML validity, key
integrity) is Epic #6. This module implements only the walking skeleton's
minimal slice (issue #71/#73/#44/#48): placeholder-preservation checks
(positional `{0}`/`{1}`/… and named `{PAWN_x}`-style GrammarResolver
tags), composed behind one orchestrator entry point so later Epic #6 work
extends this same seam instead of introducing a second one.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from rimtrans.core.models import SourceString, TranslationResult

_POSITIONAL_RE = re.compile(r"\{(\d+)\}")
_NAMED_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """Pass/fail plus the specific reasons for every failed check."""

    passed: bool
    failures: tuple[str, ...] = ()


def _diff_counts(label: str, source: Counter[str], translated: Counter[str]) -> list[str]:
    failures: list[str] = []
    missing = source - translated
    extra = translated - source
    for token, count in sorted(missing.items()):
        failures.append(f"{label} token {{{token}}} missing {count}x in translation")
    for token, count in sorted(extra.items()):
        failures.append(f"{label} token {{{token}}} appears {count}x extra in translation")
    return failures


def check_placeholders(source_text: str, translated_text: str) -> list[str]:
    """Check positional `{0}`/`{1}`/… and named `{PAWN_x}` tokens are preserved.

    Reordering is fine (Russian word order may legitimately differ); the
    set and count of each mechanism's tokens must match exactly. The two
    mechanisms are checked independently so failure messages distinguish
    which one broke (`RIMWORLD_LOCALIZATION.md` §5(a)-(b)).
    """
    failures: list[str] = []
    failures += _diff_counts(
        "positional",
        Counter(_POSITIONAL_RE.findall(source_text)),
        Counter(_POSITIONAL_RE.findall(translated_text)),
    )
    failures += _diff_counts(
        "named",
        Counter(_NAMED_RE.findall(source_text)),
        Counter(_NAMED_RE.findall(translated_text)),
    )
    return failures


def validate(source: SourceString, result: TranslationResult) -> ValidationOutcome:
    """Minimal validation orchestrator: placeholder-preservation only.

    The single entry point both the router (Epic #5) and `rimtrans
    validate` (Epic #9) will call once they exist (issue #48) — this
    walking-skeleton version runs only the placeholder check; Epic #6
    adds the remaining gates behind this same function.
    """
    failures = check_placeholders(source.source_text, result.translated_text)
    return ValidationOutcome(passed=not failures, failures=tuple(failures))
