"""The `TranslationProvider` interface (`ARCHITECTURE.md` §6).

The router (Epic #5) never hard-codes a specific model — every local
(Epic #4) and remote (Epic #5) backend implements this same `Protocol`.
Structural typing (rather than an ABC) is deliberate: a provider doesn't
need to import this module to satisfy the interface, only to match its
shape, which keeps provider implementations decoupled from `core`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from rimtrans.core.models import (
    GlossaryRules,
    ProviderCapabilities,
    ProviderKind,
    SemanticContext,
    SourceString,
    TranslationResult,
)


@runtime_checkable
class TranslationProvider(Protocol):
    """A local or remote backend capable of translating a batch of strings."""

    id: str
    kind: ProviderKind
    capabilities: ProviderCapabilities

    def translate(
        self,
        batch: Sequence[SourceString],
        context: SemanticContext,
        glossary: GlossaryRules,
    ) -> list[TranslationResult]:
        """Translate `batch`, honoring `context` and `glossary`.

        Implementations should return exactly one `TranslationResult` per
        input `SourceString`, in the same order.
        """
        ...
