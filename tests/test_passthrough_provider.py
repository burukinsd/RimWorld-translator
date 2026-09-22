"""Trivial pass-through provider tests (issue #72)."""

from __future__ import annotations

from rimtrans.core.models import (
    Domain,
    GlossaryRules,
    ProviderKind,
    SemanticContext,
    SourceString,
    ValidationStatus,
)
from rimtrans.core.provider import TranslationProvider
from rimtrans.providers.passthrough import PassthroughProvider
from rimtrans.validator import check_placeholders


def test_passthrough_provider_satisfies_the_protocol() -> None:
    assert isinstance(PassthroughProvider(), TranslationProvider)


def test_passthrough_provider_metadata() -> None:
    provider = PassthroughProvider()
    assert provider.id == "skeleton:passthrough"
    assert provider.kind == ProviderKind.LOCAL


def test_output_is_deterministically_different_from_input() -> None:
    provider = PassthroughProvider()
    batch = [
        SourceString(mod_id="m", domain=Domain.KEYED, key_path="A", source_text="Hello world"),
        SourceString(
            mod_id="m",
            domain=Domain.KEYED,
            key_path="B",
            source_text="{0} recruited {1}.",
        ),
    ]

    results = provider.translate(batch, SemanticContext(), GlossaryRules())

    assert len(results) == 2
    for source, result in zip(batch, results, strict=True):
        assert result.translated_text != source.source_text
        assert source.source_text in result.translated_text
        assert result.provider_id == "skeleton:passthrough"
        assert result.validation_status == ValidationStatus.PENDING


def test_output_is_deterministic_across_calls() -> None:
    provider = PassthroughProvider()
    batch = [SourceString(mod_id="m", domain=Domain.KEYED, key_path="A", source_text="Hi")]

    first = provider.translate(batch, SemanticContext(), GlossaryRules())
    second = provider.translate(batch, SemanticContext(), GlossaryRules())

    assert first[0].translated_text == second[0].translated_text


def test_output_preserves_all_placeholders() -> None:
    provider = PassthroughProvider()
    batch = [
        SourceString(
            mod_id="m",
            domain=Domain.KEYED,
            key_path="A",
            source_text="{0} greets {PAWN_nameDef}.",
        )
    ]

    results = provider.translate(batch, SemanticContext(), GlossaryRules())

    assert check_placeholders(batch[0].source_text, results[0].translated_text) == []
