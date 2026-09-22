"""Trivial pass-through provider for skeleton validation (issue #72).

A fake `TranslationProvider` that performs a deterministic, non-model
transform, used solely to prove the walking-skeleton pipeline's end-to-end
shape (issue #73) without depending on live local-model infrastructure
(GPU/Ollama). Replaced by the real TranslateGemma-via-Ollama provider once
the skeleton is proven (issue #75).
"""

from __future__ import annotations

from collections.abc import Sequence

from rimtrans.core.models import (
    GlossaryRules,
    ProviderCapabilities,
    ProviderKind,
    SemanticContext,
    SourceString,
    TranslationResult,
)

_PREFIX = "[RU] "
PROMPT_VERSION = "passthrough-v1"


class PassthroughProvider:
    """Deterministically prefixes each source string — not a real translation.

    The transform never touches token content, so placeholders/tags are
    preserved by construction.
    """

    id = "skeleton:passthrough"
    kind = ProviderKind.LOCAL
    capabilities = ProviderCapabilities(structured_output=False, max_batch_size=256)

    def translate(
        self,
        batch: Sequence[SourceString],
        context: SemanticContext,
        glossary: GlossaryRules,
    ) -> list[TranslationResult]:
        return [
            TranslationResult(
                source=item,
                translated_text=f"{_PREFIX}{item.source_text}",
                provider_id=self.id,
                prompt_version=PROMPT_VERSION,
            )
            for item in batch
        ]
