# RimWorld LLM Translation Compiler

An offline-first localization compiler for RimWorld 1.6. Point it at a large
modlist (built for ~180 mods), and it scans the installed mods, extracts
English localization, diffs it against a persistent Translation Memory and
any existing Russian localization, translates through a hybrid local/remote
LLM pipeline with glossary and validation, and generates a **standalone**
Russian translation mod — never touching the original Workshop mods.

Think of it as a "DDS converter for localization": scan, compile, ship a
ready-to-use translation pack.

```
RimWorld Mods → scan → extract EN → diff (TM + existing RU) → glossary
   → local LLM → validate → remote LLM (hard cases) → human review
   → standalone Russian translation mod
```

## Status

**Foundation stage (Epic #1).** The project skeleton — package layout,
config loading, logging/error conventions, the `rimtrans` CLI (all
subcommands registered but stubbed), CI, and the shared core interfaces —
is in place; no real extraction/translation/validation/generation logic
exists yet (that's Epic #2 onward). The full architecture, RimWorld 1.6
localization research, local/remote translation model research, and
phased implementation roadmap are documented in [`docs/`](docs/), and the
implementation plan is tracked as GitHub Issues.

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design, component
  breakdown, Translation Memory schema, hybrid routing strategy, validation
  rules, benchmark subsystem, CLI, generated-mod structure.
- [`docs/RIMWORLD_LOCALIZATION.md`](docs/RIMWORLD_LOCALIZATION.md) —
  researched, cited notes on RimWorld 1.6's actual `DefInjected`/`Keyed`/
  `Strings` structure, `About.xml` conventions, placeholder/escaping rules,
  and prior-art tooling.
- [`docs/LLM_TRANSLATION.md`](docs/LLM_TRANSLATION.md) — researched,
  cited comparison of local (TranslateGemma, OPUS-MT, NLLB, Qwen, RU-native
  models) and remote (Claude, GPT, Gemini, DeepL) translation options, and
  benchmark methodology.
- [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) — phased
  roadmap (Phase 0–15) mapping to the GitHub Epics/Issues.

## Design principles

- **Never modify original mods.** All output goes into a separate,
  generated translation mod, following the standard RimWorld
  `loadAfter`-based translation-addon pattern.
- **Provider-independent translation.** No local or remote model is
  hard-coded as "the" translator. A benchmark subsystem measures real
  candidates (quality, placeholder safety, latency, cost, VRAM) and the
  choice is a config value, not an assumption — TranslateGemma is a strong
  candidate per research, but it is not pre-selected.
- **Incremental by design.** Unchanged strings are never re-translated.
  Translation Memory tracks a hash of each source string so mod updates
  (added/removed/reworded Defs) are detected and only the affected strings
  re-enter the pipeline.
- **Validation is a hard gate, not a quality score.** Every generated
  translation is checked for placeholder/tag/escape/XML integrity before it
  can enter the generated mod. A broken placeholder is a build failure, not
  a style nit.
- **Minimize cloud usage.** The hybrid router prefers Translation Memory →
  glossary → local model, escalating to remote LLMs only for strings that
  fail validation or are flagged difficult.

## Planned CLI

```
rimtrans scan         rimtrans diff        rimtrans translate
rimtrans validate      rimtrans build       rimtrans report
rimtrans glossary      rimtrans benchmark
```

See `docs/ARCHITECTURE.md` §10 for details, including the planned dry-run
mode (translation-memory reuse, local/remote work split, token/cost
estimates).

## Development

Requires Python 3.11+.

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

rimtrans --help                          # CLI, all commands stubbed for now
rimtrans --config config/example.yaml scan

ruff check .                             # lint
mypy                                      # type-check
pytest                                    # test
```

See [`docs/adr/`](docs/adr/) for the toolchain, logging/error-handling, and
core-interface decisions this scaffolding is built on.

## Contributing

Implementation work is tracked as GitHub Issues, grouped under 12 Epics
covering architecture/foundation, RimWorld localization extraction,
Translation Memory & glossary, local translation models, LLM providers &
hybrid routing, validation & QA, incremental translation, translation mod
generation, CLI & reporting, model benchmarking, large-modlist integration,
and future runtime translation. Each implementation Issue is scoped to be
small enough for a coding agent (or contributor) to pick up independently,
with explicit dependencies on other Issues called out.
