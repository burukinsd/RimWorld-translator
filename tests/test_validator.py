"""Placeholder validator tests (issue #44/#48, walking-skeleton scope)."""

from __future__ import annotations

import pytest

from rimtrans.core.models import Domain, SourceString, TranslationResult
from rimtrans.validator import check_placeholders, validate


@pytest.mark.parametrize(
    ("source", "translated", "expected_failures"),
    [
        ("{0} recruited {1}.", "{1} завербовал {0}.", 0),  # reordering is fine
        ("Hello {0}!", "Привет!", 1),  # missing positional
        ("Hello!", "Привет {0}!", 1),  # extra positional
        ("{0} and {0}", "{0}", 1),  # wrong count (missing one occurrence)
        ("{PAWN_nameDef} arrived.", "{PAWN_nameDef} прибыл.", 0),
        ("{PAWN_nameDef} arrived.", "Прибыл кто-то.", 1),  # missing named tag
        ("Arrived.", "{PAWN_nameDef} прибыл.", 1),  # extra named tag
        ("{PAWN_nameDef}", "{pawn_namedef}", 2),  # casing mismatch: missing + extra
        ("{0} {PAWN_nameDef}", "{0} {PAWN_nameDef}", 0),  # both mechanisms together
    ],
)
def test_check_placeholders_table(source: str, translated: str, expected_failures: int) -> None:
    failures = check_placeholders(source, translated)
    assert len(failures) == expected_failures


def test_check_placeholders_distinguishes_positional_from_named_in_message() -> None:
    failures = check_placeholders("Hello {0}!", "Привет!")
    assert any("positional" in f for f in failures)

    failures = check_placeholders("{PAWN_nameDef} arrived.", "Прибыл.")
    assert any("named" in f for f in failures)


def _make_result(source_text: str, translated_text: str) -> tuple[SourceString, TranslationResult]:
    source = SourceString(mod_id="mod", domain=Domain.KEYED, key_path="K", source_text=source_text)
    result = TranslationResult(
        source=source, translated_text=translated_text, provider_id="p", prompt_version="v1"
    )
    return source, result


def test_validate_passes_when_placeholders_preserved() -> None:
    source, result = _make_result("{0} recruited {1}.", "[RU] {0} recruited {1}.")

    outcome = validate(source, result)

    assert outcome.passed is True
    assert outcome.failures == ()


def test_validate_fails_when_placeholder_dropped() -> None:
    source, result = _make_result("{0} recruited {1}.", "[RU] recruited someone.")

    outcome = validate(source, result)

    assert outcome.passed is False
    assert len(outcome.failures) == 2  # both {0} and {1} missing
