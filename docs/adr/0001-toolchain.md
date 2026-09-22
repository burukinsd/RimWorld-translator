# ADR 0001: Toolchain — Python 3.11+

- Status: Accepted
- Related: Epic #1 (Architecture & Foundation), issue #13

## Context

`docs/ARCHITECTURE.md` is deliberately language-agnostic. Before any real
component (scanner, extractor, TM, router, providers, validator, generator,
CLI) can be built, the project needs one concrete toolchain choice. The
requirements driving the choice, per issue #13:

- Strong SQLite support (Translation Memory, §5 of `ARCHITECTURE.md`).
- Good XML handling (`DefInjected`/`Keyed` extraction, per
  `RIMWORLD_LOCALIZATION.md`).
- A first-class HTTP client for local model servers (Ollama's
  OpenAI-compatible API, a CTranslate2 server) and remote LLM/DeepL APIs.
- A CLI framework with subcommand support, matching the `rimtrans <command>`
  surface in `ARCHITECTURE.md` §10.
- An ecosystem well-suited to Epic 10/13's benchmark subsystem (scoring,
  local model tooling) and Epic 4's local-model integrations
  (llama.cpp/Ollama/CTranslate2 all have first-class Python bindings or
  clients).

## Decision

**Python 3.11+**, with:

| Concern | Choice | Why |
|---|---|---|
| CLI framework | [Typer](https://typer.tiangolo.com/) (built on Click) | Subcommands, auto-generated `--help`, typed options — fits `ARCHITECTURE.md` §10 directly. |
| Config validation | [Pydantic v2](https://docs.pydantic.dev/) | Schema-as-code with clear, field-level validation errors (issue #14's "specific, actionable error message" requirement). |
| Config file format | YAML (via `PyYAML`) | Supports comments, which a documented example config (issue #14) needs; ubiquitous for this kind of tool config. |
| Translation Memory | stdlib `sqlite3` | No extra dependency; mature, sufficient for Epic 3's schema. |
| XML extraction | stdlib `xml.etree.ElementTree` for MVP | Sufficient for the `DefInjected`/`Keyed` shapes documented in `RIMWORLD_LOCALIZATION.md`; revisit `lxml` in Epic 2 only if XPath/namespace edge cases demand it. |
| HTTP client | `httpx` (added when Epic 4/5 first need it) | Modern, typed, supports both sync and async; not added as a dependency yet since Epic 1 makes no HTTP calls — avoids an unused dependency. |
| Structured logging | stdlib `logging` + a JSON formatter (see ADR 0002) | No new dependency; structured fields via `extra=`. |
| Lint / format | `ruff` | Fast, single tool for both. |
| Type-check | `mypy` | Standard, works well with Pydantic v2. |
| Tests | `pytest` | Standard. |

## Alternatives considered

- **TypeScript/Node** — also viable (`commander`/`oclif`, `better-sqlite3`,
  `fast-xml-parser`). Rejected in favor of Python because Epic 4/10/13
  (local model integration, benchmarking) lean heavily on an ecosystem
  Python already has first-class clients/bindings for (Ollama's Python
  client, CTranslate2's Python API, llama.cpp Python bindings), avoiding a
  second language boundary between the pipeline and the model layer.
- **Go** — excellent CLI ergonomics and a single static binary, but SQLite
  support requires either cgo or a less mature pure-Go driver, and the
  local-model ecosystem (Epic 4) is far thinner than Python's.
- **Rust** — strong performance and correctness guarantees, but slower
  development velocity for a project built incrementally across many
  small, independently-scoped Issues (per issue #17's context on parallel
  coding-agent contributors), and the same thin local-model ecosystem
  problem as Go.

## Directory layout

Package layout (`src/rimtrans/`) mirrors the component breakdown in
`ARCHITECTURE.md` §2. Each package below is scaffolded as an empty/stub
module in this Epic; the referenced Epic owns its real implementation.

```
src/rimtrans/
├─ cli/            # CLI entry point and commands (Epic 1, issue #16)
├─ config/         # Config schema + loader (Epic 1, issue #14)
├─ core/           # Shared domain interfaces (Epic 1, issue #18)
├─ scanner/        # Mod discovery, version resolution (Epic 2)
├─ extractor/       # DefInjected/Keyed/Strings extraction (Epic 2)
├─ tm/              # Translation Memory, SQLite schema (Epic 3)
├─ router/          # Hybrid Translation Router (Epic 5)
├─ providers/        # Local + remote TranslationProvider implementations (Epic 4, 5)
├─ validator/        # Placeholder/tag/XML validation gates (Epic 6)
├─ generator/         # Deterministic translation-mod builder (Epic 8)
├─ errors.py          # Shared error hierarchy (Epic 1, issue #15)
├─ log.py             # Logging setup + structured formatter (Epic 1, issue #15)
└─ batch.py           # Recoverable-error batch-processing helper (Epic 1, issue #15)
```

The Glossary (Epic 3) and benchmark subsystem (Epic 10) are cross-cutting
per `ARCHITECTURE.md` §2 and will live under `tm/glossary` and a new
`benchmark/` package respectively when their Epics start — not scaffolded
here to avoid empty packages nothing in this Epic references.

## Acceptance

- `rimtrans --help` runs and prints the CLI's `--help` output (the "hello
  world" entry point for a CLI-shaped tool) — see issue #16.
- Directory layout matches the table above.
