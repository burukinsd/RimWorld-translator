# Implementation Plan — Phased Roadmap

This roadmap maps to the GitHub Epics and Issues created alongside this
document. Phases are mostly sequential but Phases 4–6 (Translation Memory,
Glossary, Local LLM providers) can proceed in parallel once Phase 1
(foundation) and Phase 2 (extraction) land, since they don't depend on each
other directly. Each phase corresponds to one or more Epics; see the Epic
issues for the authoritative, up-to-date breakdown into implementable
Issues — this document is the narrative overview.

**Delivery strategy — walking skeleton.** The phase list below is organized
by architectural layer (foundation → extraction → TM/glossary → local
models → routing → validation → incremental → generation → CLI → benchmark
→ scale → future), which is a sound engineering decomposition but means no
end-user-visible result — an actual installable translated mod — would
otherwise exist until Phase 11 is complete. **Phase 1.5** deliberately
breaks that: it pulls a minimal-scope slice of Phases 2, 6, 8, and 11
forward into one thin, fully end-to-end pass (single mod, `Keyed`-only,
one provider, placeholder-only validation, single-mod output) so a real
installable mod exists almost immediately after the foundation lands.
Every later phase then broadens or hardens one stage of that already-working
pipeline instead of building components in isolation with nothing runnable
until late. See GitHub Epic "Walking Skeleton — First Installable Mod"
(#71) for the concrete issues, and the per-Epic "Sequencing note" sections
added to Epics 1–6, 8, and 9 for how each phase's issues relate to it.

## Phase 0 — Research & architecture (this session)

Repository inspection, RimWorld 1.6 localization research, local/remote
translation-model research, architecture design, documentation, and GitHub
Issue planning. **No production code.** Output: `ARCHITECTURE.md`,
`RIMWORLD_LOCALIZATION.md`, `LLM_TRANSLATION.md`, this document, and the
GitHub Epics/Issues.

## Phase 1 — Project foundation

Establish the project skeleton: language/toolchain choice, package
structure, config loading, logging, error handling conventions, CI
scaffolding, and the CLI entry point shape (commands registered but mostly
stubbed). Nothing here does real extraction or translation yet — it's the
scaffolding every later phase builds on.

## Phase 1.5 — Walking skeleton (first installable mod)

A thin, fully end-to-end pass through the whole architecture, proven by
installing the result in a real RimWorld 1.6 instance, before any phase
below is built out to its full scope:

1. Minimal mod scan (single hardcoded local test mod, not full Workshop
   discovery — that's Phase 2's job).
2. Minimal extraction (`Keyed/` only, not `DefInjected`/`Strings` yet —
   Phase 2's job).
3. A trivial pass-through/deterministic-transform provider, so the first
   proof doesn't depend on live local-model infrastructure (GPU/Ollama) —
   followed immediately by a fast-follow swapping in a real local provider
   (TranslateGemma via Ollama, pulled forward from Phase 6).
4. Minimal validation (placeholder-preservation check only, pulled forward
   from Phase 8; the full gate set is still Phase 8's job).
5. Minimal generation (single mod, `Keyed`-only output, basic `About.xml`,
   pulled forward from Phase 11; multi-mod namespacing is still Phase 11's
   job).
6. Real-game proof: install the generated mod in RimWorld 1.6 and confirm
   translated text is visible.

No new architecture is introduced here, and nothing built in this phase is
throwaway — each piece is the literal starting point the corresponding
later phase broadens. Tracked as GitHub Epic #71, with its critical-path
issues (in Epics 1, 2, 4, 6, 8) tagged `walking-skeleton`.

## Phase 2 — RimWorld localization extraction

Mod scanner (Workshop + local install discovery, version resolution) and
the extractor for `DefInjected`, `Keyed`, and `Strings`. Includes the
config-driven translatable-field-path table for common Def types (§3, §12
of `ARCHITECTURE.md`). Validates against real installed mods, not just
synthetic fixtures — this phase is where the "Open items to verify" list at
the end of `RIMWORLD_LOCALIZATION.md` gets closed out.

## Phase 3 — Russian localization + diff

Reads any existing `Languages/Russian/` content a mod already ships (or a
third-party RU translation mod covering it), and diffs extracted English
against it and against Translation Memory state. Produces the "what's
new/changed/stale" report that `rimtrans diff` exposes.

## Phase 4 — Translation Memory

SQLite schema (§5 of `ARCHITECTURE.md`), migrations, the hash-based
staleness mechanism, and the read/write API the router and generator both
depend on. This is the persistence backbone for the incremental-update
guarantee.

## Phase 5 — Glossary

Global / mod-specific / semantic-type glossary storage and lookup,
preferred-translation and forbidden-alternative support, and the CLI
surface (`rimtrans glossary`).

## Phase 6 — Local LLM providers

Provider abstraction (§6 of `ARCHITECTURE.md`), the chat/instruct backend
(Ollama-compatible), and the encoder-decoder/CTranslate2 backend (for
OPUS-MT and similar). At least two concrete providers implemented
end-to-end (e.g. one TranslateGemma-family model via Ollama, one OPUS-MT
via CTranslate2) to prove the abstraction holds, without yet picking a
"default" — that's a Phase 13 benchmark decision.

## Phase 7 — Batch translation

Wires extraction → TM lookup → glossary → local provider into a working
batch pipeline for the common case (no remote calls, no validation
escalation yet — those are Phases 8–9). Produces draft translations sitting
in TM with `validation_status = pending`.

## Phase 8 — Validation

The deterministic validator (§8 of `ARCHITECTURE.md`): placeholders, named
tags, RulePack symbols, rich text, escape sequences, XML validity, key
integrity. Runs as a gate on every provider output, local or remote,
including every retry. `rimtrans validate` becomes usable standalone against
existing TM state.

## Phase 9 — Hybrid routing

The full Translation Router (§4): TM hit → glossary → local → validate →
remote escalation → human review, with configurable escalation triggers
(validation failure, low-confidence heuristics, always-escalate semantic
types). Remote provider adapters (at least one LLM-based and, if in scope,
DeepL) implemented against the same provider interface as local models.

## Phase 10 — Incremental updates

Hardens the staleness/rebuild path end-to-end against a real changing mod
(orphaned keys, new keys, reworded English text) and against Translation
Memory growth over repeated builds at 180-mod scale. Surfaces orphaned-key
cleanup reporting.

## Phase 11 — Translation mod generation

Deterministic mod builder (§11 of `ARCHITECTURE.md`): namespaced output
tree, `About.xml` generation with correct `loadAfter`/`modDependencies`,
byte-identical output for identical inputs. `rimtrans build` becomes fully
usable.

## Phase 12 — CLI / reporting

Fills in the remaining CLI surface and polish: `rimtrans report`, dry-run
mode (§10) with token/cost estimation, coverage reporting, and general UX
(progress output, resumability of long batch runs).

## Phase 13 — Model benchmark

The benchmark subsystem (§9 of `ARCHITECTURE.md`): representative corpus
curation, placeholder-integrity gate, chrF++/COMET-class scoring, latency/
VRAM/throughput/cost/failure-rate measurement across every registered
provider. `rimtrans benchmark` becomes usable. **This is where a default
local model gets chosen from evidence, not assumption** — TranslateGemma is
a strong candidate per research but is not pre-selected.

## Phase 14 — Large modlist integration

End-to-end validation against a real ~180-mod modlist: performance at
scale, TM growth/vacuum strategy, batching/throughput tuning informed by
Phase 13's numbers, and resilience (partial failures, resumable runs,
Workshop mods updating mid-run).

## Phase 15 — Future runtime translation (research only within MVP scope)

Explicitly deferred (§12 of `ARCHITECTURE.md`). The semantic-type/provider
abstraction is designed to extend here, but no implementation work happens
in MVP. This phase exists in the roadmap so the architecture is not
accidentally designed in a way that forecloses it later.

## Sequencing notes

- Phase 1.5 (walking skeleton) should run immediately after Phase 1 and
  before deep work on Phases 2–12. It is a strongly recommended build-order
  prerequisite, not a hard blocker: it pulls forward the minimal-scope
  slice of a handful of issues from Phases 2, 6, 8, and 11 (tagged
  `walking-skeleton` in GitHub) to prove the pipeline shape and produce a
  real installable mod early. Those same issues' full acceptance criteria
  remain the responsibility of their home phase.
- Phases 2–3 must land before 4–9 can be meaningfully tested end-to-end
  (they need real extracted strings to operate on), but Phase 4's schema
  design and Phase 6's provider abstraction can be designed/started in
  parallel with Phase 2/3 implementation once Phase 1 lands, since they
  don't structurally depend on extraction output shape beyond the
  `SourceString`/`TranslationResult` interfaces defined in Phase 1.
- Phase 8 (validation) should land **before** Phase 9 (hybrid routing) is
  considered complete, since routing's escalation trigger depends on
  validation results — but a minimal validator can and should exist by
  Phase 7 so draft translations are never treated as "done" without at
  least the hard gates applied.
- Phase 13 (benchmark) is written after Phases 6/7/9 provide working
  providers and a pipeline to measure, but the benchmark *subsystem's*
  interfaces should be sketched early (Phase 6) so providers are built
  benchmark-ready from the start rather than retrofitted.
