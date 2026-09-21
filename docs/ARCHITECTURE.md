# Architecture — RimWorld LLM Translation Compiler

Status: **planning**. No production code has been implemented yet. This
document is the technical design that the Implementation Plan
(`IMPLEMENTATION_PLAN.md`) and the GitHub Issues break into buildable units.

## 1. Product framing

An offline-first localization compiler for RimWorld 1.6, sized for a large
modlist (~180 mods). Think "DDS converter for localization": scan the mods
you have installed, compile a translation, produce a ready-to-use pack. It
never modifies the mods it reads.

```
RimWorld Mods (Workshop + local)
   → scan
   → extract English localization (DefInjected / Keyed / Strings)
   → read existing Russian localization (if any mod ships one)
   → diff against Translation Memory
   → glossary application
   → local LLM translation
   → validation
   → remote LLM for flagged/difficult cases
   → human review
   → generate standalone Russian translation mod
```

Hard constraint: **the tool only ever writes to its own output mod
directory.** Source mods (Workshop or local) are read-only inputs.

## 2. System components

```
┌──────────────┐   ┌───────────────┐   ┌──────────────────┐
│  Mod Scanner  │ → │   Extractor   │ → │  Diff / Change    │
│ (discovery,   │   │ (DefInjected, │   │  Detection        │
│  version      │   │  Keyed,       │   │ (vs. TM + vs.     │
│  resolution)  │   │  Strings)     │   │  existing RU)     │
└──────────────┘   └───────────────┘   └─────────┬─────────┘
                                                   ↓
                                      ┌────────────────────────┐
                                      │   Translation Memory    │
                                      │   (SQLite, persistent)  │
                                      └───────────┬─────────────┘
                                                   ↓
                                      ┌────────────────────────┐
                                      │   Translation Router     │
                                      │ (TM hit? glossary rule?  │
                                      │  local model? escalate?) │
                                      └──┬───────┬──────┬───────┘
                        ┌─────────────────┘       │      └───────────────┐
                        ↓                          ↓                      ↓
              ┌──────────────────┐      ┌──────────────────┐   ┌──────────────────┐
              │   Local LLM(s)    │      │     Glossary      │   │   Remote LLM(s)   │
              │ (Ollama/llama.cpp │      │ (global/mod/       │   │ (Claude/GPT/      │
              │  provider(s))     │      │  semantic-type)     │   │  Gemini/DeepL)     │
              └────────┬──────────┘      └─────────┬──────────┘   └─────────┬──────────┘
                        └───────────────────┬───────┴────────────────────────┘
                                             ↓
                                  ┌────────────────────┐
                                  │      Validator       │
                                  │ (placeholders, tags,  │
                                  │  XML, escapes, keys)  │
                                  └──────────┬────────────┘
                                             ↓
                                  ┌────────────────────┐
                                  │  Review / Accept     │
                                  │ (auto-accept high-    │
                                  │  confidence, else      │
                                  │  human queue)          │
                                  └──────────┬────────────┘
                                             ↓
                                  ┌────────────────────┐
                                  │   Mod Generator      │
                                  │ (deterministic        │
                                  │  Languages/Russian/   │
                                  │  tree + About.xml)    │
                                  └────────────────────┘
```

Cross-cutting: **Benchmark subsystem** (measures any provider — local or
remote — against a fixed corpus, feeds router confidence thresholds) and
**CLI/Reporting** (drives every stage, dry-run, cost/token estimation).

## 3. Extraction layer

Follows the confirmed structure in `RIMWORLD_LOCALIZATION.md`. Three
first-class localization domains, in priority order for MVP:

1. **DefInjected** — `<DefName.fieldPath>` keys, grouped by Def type folder.
   Extraction needs both XML scanning (`Defs/`) and ideally field-level
   knowledge of which fields are translatable per Def type (RimTrans's
   prior-art lesson: pure text scanning under-discovers translatable
   fields). MVP approach: a maintained table of well-known translatable
   field paths per common Def type (`label`, `description`, `labelFemale`,
   `stages.N.label`, …), extensible via config rather than requiring C#
   reflection over mod DLLs (out of scope — see §11).
2. **Keyed** — flat key→value, extracted directly from
   `Languages/English/Keyed/*.xml`.
3. **Strings** — plain `.txt` line pools. No stable per-entry key; addressed
   by `(file, line index)`. Lower priority; incremental re-translation is
   inherently weaker here (§8 of the localization doc) — MVP treats a
   changed file as "re-diff all lines in that file" rather than pretending
   per-line stability it doesn't have.

Each extracted entry carries: source mod id, localization domain, Def type
(if applicable), key/path, raw English value, and a **semantic type** (§7)
derived from the Def type or Keyed-key naming convention.

The extractor reads **both** the source mod's `Languages/English/` (or its
inferred defaults from `Defs/` when a mod ships no English localization at
all — a common case) **and**, if present, the mod's own
`Languages/Russian/` (or a third-party RU translation mod already covering
it) to seed the diff step — never overwriting an existing human translation
without going through the same diff/review pipeline as everything else.

## 4. Translation Router — hybrid strategy

Preferred resolution order, per string:

1. **Exact Translation Memory match** — `source_hash` for this
   `(source_lang, target_lang, normalized_source, semantic_type)` already
   has an `accepted`/`validated` row → reuse, no model call.
2. **Glossary/rule reuse** — if the string is (or reduces to, after
   placeholder-masking) a glossary term or a short templated fragment
   covered by a rule, apply directly.
3. **Local model** — default engine call (model choice is a config/benchmark
   decision, not hard-coded; see `LLM_TRANSLATION.md`).
4. **Validation** — every model output passes the validator (§8) before it
   is eligible for acceptance.
5. **Remote LLM escalation** — triggered when: validation fails on the
   local output after N retries, the router's confidence heuristic flags
   the string as "difficult" (long/ambiguous, heavy grammar-rule content,
   low agreement between two local passes), or the string belongs to a
   semantic type configured as always-escalate (e.g. quest text).
6. **Human review** — anything that fails validation even after remote
   escalation, or that policy marks as always-review (e.g. legal/credits
   text, or a user-configured "review everything" mode for a mod).

Goal: minimize cloud usage while never letting an invalid translation reach
the generated mod silently. The router is provider-agnostic — see §6.

## 5. Translation Memory (SQLite)

Persistent, incremental by design. Proposed schema (illustrative — exact
column types/indices are a Phase 4 implementation detail):

```sql
CREATE TABLE translation_memory (
    id                  INTEGER PRIMARY KEY,
    source_lang         TEXT NOT NULL,          -- 'en'
    target_lang         TEXT NOT NULL,          -- 'ru'
    source_text         TEXT NOT NULL,          -- raw extracted English value
    normalized_source    TEXT NOT NULL,          -- placeholder-masked, whitespace-normalized
    source_hash         TEXT NOT NULL,          -- hash(normalized_source) — staleness key
    translation         TEXT,                    -- current accepted RU value, nullable pre-translation
    mod_id              TEXT NOT NULL,          -- source mod package id
    mod_version         TEXT,                    -- source mod's declared version, if known
    domain              TEXT NOT NULL,          -- 'DefInjected' | 'Keyed' | 'Strings'
    def_type            TEXT,                    -- e.g. 'ThingDef', null for Keyed/Strings
    key_path             TEXT NOT NULL,          -- e.g. 'Beer.label' or 'RecruitSuccess'
    semantic_type        TEXT,                    -- e.g. 'thing_label', 'research_project', 'quest_text'
    provider             TEXT,                    -- e.g. 'local:translategemma-12b', 'remote:claude-sonnet'
    prompt_version        TEXT,                    -- prompt template id + version, for reproducibility
    validation_status     TEXT NOT NULL DEFAULT 'pending', -- pending|passed|failed
    review_status         TEXT NOT NULL DEFAULT 'unreviewed', -- unreviewed|auto_accepted|human_accepted|rejected
    created_at            TEXT NOT NULL,
    updated_at            TEXT NOT NULL,
    UNIQUE(source_lang, target_lang, normalized_source, semantic_type, mod_id)
);

CREATE INDEX idx_tm_source_hash ON translation_memory(source_hash);
CREATE INDEX idx_tm_mod ON translation_memory(mod_id, domain, key_path);
CREATE INDEX idx_tm_review_status ON translation_memory(review_status);
```

**Staleness / incremental updates** (per the `ElHanko` precedent in
`RIMWORLD_LOCALIZATION.md` §8): a rebuild recomputes `source_hash` for every
currently-extracted key. If the TM row's `source_hash` no longer matches,
the entry is marked stale and re-enters the router at step 1 (TM lookup
naturally misses, since the hash-keyed lookup no longer matches) — the
previous translation is retained in TM history for reference/diffing, not
destroyed. Unchanged strings are never re-translated: this is the core
"incremental" guarantee.

A translation is deduplicated across mods by `(normalized_source,
semantic_type)` where useful (identical vanilla-derived strings reused
across many mods), while still tracked per-`mod_id`/`key_path` so the
generator can emit correct per-mod DefInjected output and so a later
mod-specific correction doesn't leak into unrelated mods unless the
glossary/TM design explicitly allows global reuse for that semantic type.

## 6. Provider abstraction

Translation must be provider-independent — the router never hard-codes a
specific model. A single interface, roughly:

```
TranslationProvider {
  id: string                     // 'local:ollama:translategemma-12b', 'remote:anthropic:claude-sonnet'
  kind: 'local' | 'remote'
  translate(batch: SourceString[], context: SemanticContext, glossary: GlossaryRules) -> TranslationResult[]
  capabilities: { structuredOutput: bool, maxBatchSize: int, ... }
}
```

Two local backend shapes are needed (per `LLM_TRANSLATION.md` §4), because
not every candidate model is a chat-format instruct model:

- **Chat/instruct backend** — Ollama's OpenAI-compatible API (or raw
  llama.cpp server), used for TranslateGemma, Qwen, Gemma 3 Instruct, Vikhr,
  T-lite, etc. Structured-output/JSON-schema mode is used where available
  to get `{translation, placeholders_preserved}`-shaped responses instead of
  parsing free text.
- **Encoder-decoder / CTranslate2 backend** — for OPUS-MT, and optionally
  NLLB-200/MADLAD-400, which are not native Ollama citizens.

Remote providers (Claude, GPT-5.x, Gemini, DeepL) implement the same
interface; DeepL's non-LLM nature means it does not support the
structured-output capability and instead relies on its own placeholder-tag
handling feature (verify against RimWorld's actual token styles before
trusting it as sufficient on its own — §8 validation runs regardless).

Provider configuration (model id, backend endpoint, quantization,
timeout/retry policy) lives in a config file, not code — swapping the
default local model is a config change, not a new build.

## 7. Glossary & semantic context

Configurable terminology, layered:

1. **Global glossary** — project-wide term mappings (`research` →
   `исследование`, `mechanoid` → `механоид`, `pawn` → `персонаж`, `hediff`
   → `состояние здоровья`, etc.), with support for preferred translations
   and explicitly forbidden alternatives.
2. **Mod-specific glossary** — overrides/additions scoped to one mod's
   package id (a mod may coin its own terminology that conflicts with the
   global default).
3. **Semantic-type terminology** — glossary entries scoped to a semantic
   type rather than a literal source string (e.g. "in `research_project`
   context, prefer X over Y").

**Semantic context**, derived from Def type / Keyed-key convention, is
passed to the LLM prompt so translation isn't done blind:

| Def type / source | Semantic type | Context hint given to the model |
|---|---|---|
| `ResearchProjectDef` | `research_project` | "This is a research project name/description in a colony-sim tech tree." |
| `HediffDef` | `medical_condition` | "This is a medical condition, injury, or implant name/description." |
| `ThingDef` | `thing_label` | "This is an item, building, or in-game object name/description." |
| `ThoughtDef` | `pawn_thought` | "This is a colonist's internal thought/mood modifier text." |
| `TraitDef` | `trait` | "This is a personality trait name/description." |
| `GeneDef` | `gene` | "This is a genetic trait name/description (biotech mechanic)." |
| Quest-related Keyed/Defs | `quest_text` | "This is narrative quest text; tone and flavor matter, escalate to remote if ambiguous." |
| Letters/messages (Keyed) | `letter_message` | "This is a UI notification/letter shown to the player; keep concise." |

This table is illustrative and config-driven, not exhaustive — extending it
to new Def types is a config change (Epic 3), and the exact set is
finalized once real extraction against representative mods surfaces the
long tail of Def types actually in use across a 180-mod list.

## 8. Validation

Every generated translation is checked **before** it is eligible for
acceptance into the Translation Memory as `validation_status = passed`.
Checks, all hard gates (fail = never silently enters the generated pack):

1. **Positional placeholders** — `{0}`, `{1}`, … set and count must match
   source exactly.
2. **Named GrammarResolver tags** — `{PAWN_nameDef}`, `{PAWN_pronoun}`, etc.
   must appear verbatim, same casing, same count.
3. **RulePack bracket symbols** — `[pawn_nameFull]`-style tokens (where
   applicable) preserved verbatim.
4. **Rich text tags** — `<b>`, `<i>`, `<color=...>` open/close pairs and
   tag names must match the source's tag set.
5. **Escape sequences** — literal `\n` preserved as the two-character
   sequence, never expanded to a real newline or double-escaped.
6. **XML validity** — the translated value, inserted back into its element,
   must produce well-formed XML (no stray unescaped `<`/`>`/`&`).
7. **Source key integrity** — the DefInjected/Keyed key path itself is
   never altered by the translation step; only the value changes.

A failed check routes the string to escalation (remote LLM) or human review
per the router policy (§4), never to silent omission or silent
pass-through of the broken value. The validator is deterministic,
rule-based code — not itself an LLM call — so it is cheap to run on every
candidate output, including every retry.

## 9. Benchmark subsystem

Per `LLM_TRANSLATION.md` §6, no metric alone is sufficient for short,
placeholder-heavy game strings. The benchmark subsystem:

1. Maintains a **representative corpus** of real RimWorld EN→RU strings
   across domains/semantic types (curated once, versioned, extensible).
2. Runs every registered provider (local and remote) against the corpus.
3. Applies the **placeholder-integrity gate** (§8 checks) as a hard
   pass/fail filter first.
4. Scores surviving output with **chrF++** (primary lexical metric) and a
   **COMET/MetricX-class reference-free QE metric** (ranking signal).
5. Records **latency, throughput, VRAM/RAM footprint, failure rate, and
   cost** (cost = 0 for local) per provider/quantization combination.
6. Never hard-codes a winner — outputs a comparison report; the router's
   default provider is a config value a human sets from that report, not a
   baked-in constant.

Exposed as `rimtrans benchmark` (§10). Designed to be extended with new
models over time without code changes to the harness itself (models are
config entries implementing the provider interface from §6).

## 10. CLI

```
rimtrans scan        # discover installed/local mods, resolve versions, report coverage
rimtrans diff         # show what's new/changed/stale vs. Translation Memory
rimtrans translate    # run the hybrid pipeline (respects router policy)
rimtrans validate     # re-run validation gates over current TM state
rimtrans build        # generate the standalone translation mod
rimtrans report        # human-readable coverage/cost/quality report
rimtrans glossary      # manage global/mod/semantic-type glossary entries
rimtrans benchmark     # run the benchmark subsystem against registered providers
```

**Dry-run mode** (available on `translate`/`build`) reports, without calling
any model or writing any file:

- strings to translate, broken down by domain/mod/semantic type
- how many resolve from Translation Memory reuse (zero-cost)
- how many would go to the local model tier
- how many the router would escalate to remote, and why
- estimated token counts and estimated cost for the remote portion

## 11. Generated translation mod

Deterministic output, following the confirmed `About.xml`/`Languages/`
conventions from `RIMWORLD_LOCALIZATION.md` §6:

```
ST_Russian_Translation/
├─ About/
│  └─ About.xml           # packageId independent of source mods; loadAfter
│                          # every translated mod's packageId; modDependencies
│                          # listing each for auto-sort/warnings
└─ Languages/
   └─ Russian/
      ├─ DefInjected/<DefType>/<mod_id>__<file>.xml
      ├─ Keyed/<mod_id>__<file>.xml
      └─ Strings/<mod_id>__<file>.txt
```

- Output filenames are namespaced by source `mod_id` to keep per-mod diffs
  reviewable and avoid collisions when two source mods happen to use the
  same upstream filename convention.
- Every emitted entry carries the `<!-- EN: ... -->` comment convention
  (§2 of the localization doc) so a human editing the generated XML
  directly always has the English source alongside it.
- `About.xml` is generated deterministically from the set of source mods
  actually translated in this build — same inputs and same TM state always
  produce byte-identical output, which is what makes the build safely
  re-runnable and diffable in version control.
- The generator only ever writes inside its own output mod directory.
  Original Workshop/local mod directories are never opened for writing.

## 12. Out of scope for MVP (explicitly deferred)

- **Runtime-generated strings** — text assembled by mod C# code at runtime
  rather than present in `Defs/`/`Keyed/`/`Strings/` at all. The
  architecture's semantic-type/provider abstraction is designed to extend
  to this later (Epic 12 — "Future Runtime Translation"), but MVP only
  covers static, extractable content.
- **DLL-embedded / hardcoded strings** — per prior-art's own stated
  limitation (`Mod-Translation-Toolkit`), these require decompilation and
  are out of scope.
- **Full RulePack/`rulesStrings` grammar-rule translation** — supported at
  the validation/preservation level (bracket symbols must survive), but
  full semantic-aware translation of generative grammar rules is a
  stretch goal, not MVP table-stakes.
- **C# reflection-based field discovery** (RimTrans's approach to finding
  translatable fields) — MVP uses a maintained, config-extensible table of
  known translatable field paths per common Def type instead; reflection
  support is a possible later enhancement if the config-table approach
  proves insufficient at 180-mod scale.

## 13. Key design decisions (summary)

| Decision | Rationale |
|---|---|
| SQLite for Translation Memory | Persistent, zero-infra, transactional, trivially portable/backup-able for a single-user offline tool. |
| Provider-agnostic router, config-driven model choice | No model (TranslateGemma included) is assumed best; benchmark subsystem drives the decision, and it can change over time without code changes. |
| Hash-keyed staleness detection | Only mechanism found in prior art (§8 of localization doc) that generalizes "Def removed," "Def added," and "English text reworded" into one check. |
| Deterministic, namespaced mod generation | Reviewable diffs, re-runnable builds, no accidental collisions across 180 source mods. |
| Hard validation gates before TM acceptance | A broken placeholder crashes/corrupts in-game formatting — never a matter of translation "quality," always a hard fail. |
| Semantic-type context in prompts | RimWorld's Def-type variety (research vs. medical vs. item vs. thought vs. trait vs. quest) genuinely changes what a correct translation looks like; blind string-in-string-out translation would systematically mistranslate ambiguous short labels. |
| Never modify source mods | Product requirement; also the only approach consistent with how RimWorld's `loadAfter` merge mechanism is designed to be used (confirmed standard community pattern). |
