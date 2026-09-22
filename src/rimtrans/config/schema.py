"""Config schema.

Anticipates the provider interface fields from `ARCHITECTURE.md` §6
(`id`, `kind`, capabilities) and the glossary layering from §7, even
though providers and the glossary itself aren't implemented until Epic #4/
#5/#3 — this is the shape those Epics consume, defined once so the config
file format doesn't need a breaking change later.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from rimtrans.core.models import ProviderKind

__all__ = [
    "GlossaryConfig",
    "ProviderConfig",
    "ProviderKind",
    "RimTransConfig",
    "RouterPolicyConfig",
    "SemanticTypeOverride",
    "TranslationMemoryConfig",
]


class ProviderConfig(BaseModel):
    """One registered translation provider (local or remote).

    Mirrors the `TranslationProvider` interface sketched in
    `ARCHITECTURE.md` §6; the concrete provider implementation
    (Epic #4/#5) looks itself up by `id`.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        min_length=1,
        description="Unique provider id, e.g. 'local:ollama:translategemma-12b'.",
    )
    kind: ProviderKind
    model: str = Field(min_length=1, description="Model identifier passed to the backend.")
    endpoint: str | None = Field(
        default=None, description="Backend endpoint URL, e.g. Ollama server."
    )
    quantization: str | None = Field(
        default=None, description="Quantization scheme, if applicable."
    )
    timeout_seconds: float = Field(default=60.0, gt=0, description="Per-request timeout.")
    max_retries: int = Field(
        default=2, ge=0, description="Retries before the router treats a call as failed."
    )


class RouterPolicyConfig(BaseModel):
    """Escalation policy knobs for the Translation Router (`ARCHITECTURE.md` §4)."""

    model_config = ConfigDict(extra="forbid")

    max_local_retries: int = Field(default=2, ge=0)
    always_escalate_semantic_types: list[str] = Field(default_factory=list)
    always_review_semantic_types: list[str] = Field(default_factory=list)
    low_confidence_escalation: bool = True


class SemanticTypeOverride(BaseModel):
    """One row of the semantic-context table from `ARCHITECTURE.md` §7.

    Config-driven and extensible, per §7: "extending it to new Def types
    is a config change." Exactly one of `def_type` /
    `keyed_key_pattern` should be set.
    """

    model_config = ConfigDict(extra="forbid")

    def_type: str | None = None
    keyed_key_pattern: str | None = Field(
        default=None, description="Regex matched against Keyed keys, e.g. '^Letter.*'."
    )
    semantic_type: str = Field(min_length=1)
    context_hint: str = Field(min_length=1)

    @model_validator(mode="after")
    def _exactly_one_selector(self) -> SemanticTypeOverride:
        if bool(self.def_type) == bool(self.keyed_key_pattern):
            raise ValueError(
                "exactly one of 'def_type' or 'keyed_key_pattern' must be set "
                f"(got def_type={self.def_type!r}, keyed_key_pattern={self.keyed_key_pattern!r})"
            )
        return self


class GlossaryConfig(BaseModel):
    """Glossary source paths (`ARCHITECTURE.md` §7). Schema owned by Epic #3."""

    model_config = ConfigDict(extra="forbid")

    sources: list[Path] = Field(default_factory=list)


class TranslationMemoryConfig(BaseModel):
    """Translation Memory location (`ARCHITECTURE.md` §5). Schema owned by Epic #3."""

    model_config = ConfigDict(extra="forbid")

    path: Path


class RimTransConfig(BaseModel):
    """Top-level rimtrans config file schema."""

    model_config = ConfigDict(extra="forbid")

    translation_memory: TranslationMemoryConfig
    glossary: GlossaryConfig = Field(default_factory=GlossaryConfig)
    providers: list[ProviderConfig] = Field(min_length=1)
    router_policy: RouterPolicyConfig = Field(default_factory=RouterPolicyConfig)
    semantic_type_overrides: list[SemanticTypeOverride] = Field(default_factory=list)

    @field_validator("providers")
    @classmethod
    def _unique_provider_ids(cls, providers: list[ProviderConfig]) -> list[ProviderConfig]:
        seen: set[str] = set()
        for provider in providers:
            if provider.id in seen:
                raise ValueError(f"duplicate provider id: {provider.id!r}")
            seen.add(provider.id)
        return providers
