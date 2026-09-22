# ADR 0003: Core domain interfaces

- Status: Accepted
- Related: Epic #1 (Architecture & Foundation), issue #18

## Context

Epic #2 produces `SourceString`s. Epics #3–#5 consume/transform them into
`TranslationResult`s via `TranslationProvider` implementations. Epic #6
validates `TranslationResult`s. Epic #8 consumes accepted ones. Getting
these shapes right now avoids a breaking change once four later Epics
depend on them.

## Decision

Defined in `rimtrans/core/models.py` and `rimtrans/core/provider.py`:

- `SourceString` — one extracted English string.
- `TranslationResult` — one candidate translation, pre-validation/review.
- `TranslationProvider` — a `typing.Protocol` every local/remote backend
  implements (structural typing, not an ABC — a provider doesn't need to
  import `core` to satisfy the interface).
- `SemanticContext` / `GlossaryRules` — minimal stubs referenced by the
  provider interface; Epic #3 owns their real implementation (semantic
  table lookup, layered glossary storage).

These are plain `@dataclass(frozen=True, slots=True)` types, not Pydantic
models: they're in-memory transport shapes produced/consumed entirely
within the process, not parsed from an external, untrusted source (that's
what the config schema, ADR-adjacent, is for) — so runtime validation
overhead isn't needed here, only static typing.

## Field mapping to the Translation Memory schema (`ARCHITECTURE.md` §5)

The TM schema itself is Epic #3's job — not built here — but these shapes
are designed to map onto it cleanly:

| `SourceString` / `TranslationResult` field | TM column | Notes |
|---|---|---|
| `SourceString.mod_id` | `mod_id` | |
| `SourceString.domain` | `domain` | `Domain` enum values match the TM `'DefInjected'\|'Keyed'\|'Strings'` check. |
| `SourceString.def_type` | `def_type` | Nullable in both. |
| `SourceString.key_path` | `key_path` | |
| `SourceString.source_text` | `source_text` | TM additionally stores `normalized_source`/`source_hash`, derived by Epic #3/#4, not carried on `SourceString` itself. |
| `SourceString.semantic_type` | `semantic_type` | Nullable until Epic #2's classifier runs. |
| `TranslationResult.translated_text` | `translation` | |
| `TranslationResult.provider_id` | `provider` | |
| `TranslationResult.prompt_version` | `prompt_version` | |
| `TranslationResult.validation_status` | `validation_status` | `ValidationStatus` enum values match the TM default/allowed values. |
| `TranslationResult.review_status` | `review_status` | `ReviewStatus` enum values match the TM default/allowed values. |

Not represented on these in-memory shapes (TM-only, set by Epic #3/#4 at
persistence time): `id`, `source_lang`/`target_lang`, `normalized_source`,
`source_hash`, `mod_version`, `created_at`, `updated_at`.

## Proof of usability

`tests/test_core_provider.py` implements a trivial fake
`TranslationProvider` (echoes the input text) purely by matching the
`Protocol`'s shape — no inheritance — and exercises `translate()` against
it, per issue #18's acceptance criteria.
