"""Core domain data shapes.

These are in-memory/transport shapes, not the Translation Memory
persistence schema (`ARCHITECTURE.md` §5, owned by Epic #3) — but they are
designed to map onto it field-for-field so Epic #3's TM rows and these
shapes don't diverge. See the mapping table in
`docs/adr/0003-core-domain-interfaces.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Domain(StrEnum):
    """Localization domain a `SourceString` was extracted from (`ARCHITECTURE.md` §3)."""

    DEF_INJECTED = "DefInjected"
    KEYED = "Keyed"
    STRINGS = "Strings"


class ProviderKind(StrEnum):
    """Whether a `TranslationProvider` runs locally or calls a remote API."""

    LOCAL = "local"
    REMOTE = "remote"


class ValidationStatus(StrEnum):
    """Validator (Epic #6) outcome for a `TranslationResult`. Mirrors TM `validation_status`."""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    """Human/auto review outcome for a `TranslationResult`. Mirrors TM `review_status`."""

    UNREVIEWED = "unreviewed"
    AUTO_ACCEPTED = "auto_accepted"
    HUMAN_ACCEPTED = "human_accepted"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class SourceString:
    """One extracted English string, ready to enter the Translation Router.

    Produced by Epic #2's extractor; field-for-field mirrors the source
    columns of the TM schema (`ARCHITECTURE.md` §5).
    """

    mod_id: str
    domain: Domain
    key_path: str
    source_text: str
    def_type: str | None = None
    semantic_type: str | None = None  # populated once Epic #2's classifier runs


@dataclass(frozen=True, slots=True)
class TranslationResult:
    """A candidate translation for a `SourceString`, pre-validation/review.

    Field-for-field mirrors the TM columns `translation`, `provider`,
    `prompt_version`, `validation_status`, `review_status`
    (`ARCHITECTURE.md` §5).
    """

    source: SourceString
    translated_text: str
    provider_id: str
    prompt_version: str
    validation_status: ValidationStatus = ValidationStatus.PENDING
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """What a `TranslationProvider` supports (`ARCHITECTURE.md` §6)."""

    structured_output: bool
    max_batch_size: int


@dataclass(frozen=True, slots=True)
class SemanticContext:
    """Context passed to a provider for one batch (`ARCHITECTURE.md` §7).

    Minimal stub — the full semantic-context table lookup is Epic #3's
    job; this is the shape providers receive once it exists.
    """

    semantic_type: str | None = None
    context_hint: str | None = None


@dataclass(frozen=True, slots=True)
class GlossaryRules:
    """Glossary terminology passed to a provider for one batch (`ARCHITECTURE.md` §7).

    Minimal stub — the layered global/mod/semantic-type glossary storage
    and lookup is Epic #3's job; this is the shape providers receive once
    it exists.
    """

    preferred_terms: dict[str, str] = field(default_factory=dict)
    forbidden_terms: dict[str, list[str]] = field(default_factory=dict)
