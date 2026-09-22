"""Shared domain interfaces every later Epic builds against.

See `rimtrans.core.models` for the data shapes and
`rimtrans.core.provider` for the `TranslationProvider` interface.
"""

from rimtrans.core.models import (
    Domain,
    GlossaryRules,
    ProviderCapabilities,
    ProviderKind,
    ReviewStatus,
    SemanticContext,
    SourceString,
    TranslationResult,
    ValidationStatus,
)
from rimtrans.core.provider import TranslationProvider

__all__ = [
    "Domain",
    "GlossaryRules",
    "ProviderCapabilities",
    "ProviderKind",
    "ReviewStatus",
    "SemanticContext",
    "SourceString",
    "TranslationProvider",
    "TranslationResult",
    "ValidationStatus",
]
