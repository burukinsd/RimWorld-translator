"""A trivial fake TranslationProvider proves the interface is usable
without needing any concrete Epic #4/#5 implementation (issue #18)."""

from __future__ import annotations

from collections.abc import Sequence

from rimtrans.core.models import (
    Domain,
    GlossaryRules,
    ProviderCapabilities,
    ProviderKind,
    SemanticContext,
    SourceString,
    TranslationResult,
    ValidationStatus,
)
from rimtrans.core.provider import TranslationProvider


class EchoProvider:
    """Fake provider: 'translates' by echoing the source text back."""

    id = "local:fake:echo"
    kind = ProviderKind.LOCAL
    capabilities = ProviderCapabilities(structured_output=True, max_batch_size=32)

    def translate(
        self,
        batch: Sequence[SourceString],
        context: SemanticContext,
        glossary: GlossaryRules,
    ) -> list[TranslationResult]:
        return [
            TranslationResult(
                source=item,
                translated_text=item.source_text,
                provider_id=self.id,
                prompt_version="echo-v1",
            )
            for item in batch
        ]


def test_echo_provider_satisfies_the_protocol() -> None:
    assert isinstance(EchoProvider(), TranslationProvider)


def test_echo_provider_translates_a_batch() -> None:
    provider = EchoProvider()
    batch = [
        SourceString(
            mod_id="RimHUD",
            domain=Domain.KEYED,
            key_path="RecruitSuccess",
            source_text="Recruitment successful.",
        ),
        SourceString(
            mod_id="RimHUD",
            domain=Domain.DEF_INJECTED,
            def_type="ThingDef",
            key_path="Beer.label",
            source_text="beer",
            semantic_type="thing_label",
        ),
    ]

    results = provider.translate(
        batch,
        context=SemanticContext(),
        glossary=GlossaryRules(),
    )

    assert len(results) == 2
    assert results[0].translated_text == "Recruitment successful."
    assert results[1].source is batch[1]
    assert results[1].provider_id == "local:fake:echo"
    assert all(r.validation_status == ValidationStatus.PENDING for r in results)
