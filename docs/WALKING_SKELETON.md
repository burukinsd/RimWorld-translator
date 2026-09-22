# Walking Skeleton — Status (Epic #71)

Records what Epic #71's walking-skeleton pass actually delivered, so later
work doesn't need to re-derive it from the issue thread. See
`IMPLEMENTATION_PLAN.md` "Phase 1.5" and `ARCHITECTURE.md` §13 for the
design rationale.

## What's implemented

- **#72 — Trivial pass-through provider**: `rimtrans.providers.passthrough.PassthroughProvider`
  (id `skeleton:passthrough`). Deterministically prefixes each string with
  `[RU] `; never touches token content, so placeholders/tags survive by
  construction.
- **#73 — Minimal end-to-end wiring**: `rimtrans.pipeline.run_translate` /
  `run_build`, exposed as `rimtrans translate --mod-path <dir> [-o <dir>]`
  and `rimtrans build [-o <dir>]`. Scans one local mod
  (`rimtrans.scanner.scan_mod`), extracts `Keyed/` only
  (`rimtrans.extractor.extract_keyed`), translates via the pass-through
  provider, validates placeholder preservation only
  (`rimtrans.validator.validate`), and generates a single-mod
  `Languages/Russian/Keyed/` tree + basic `About.xml`
  (`rimtrans.generator`). No Translation Memory yet (Epic #3) — `translate`
  persists a stateless JSON snapshot (`walking_skeleton_state.json` in the
  output directory) that `build` reads back; this is acceptable only for
  this milestone and is replaced wholesale once Epic #3 lands.

Verified by running the actual CLI against the fixture mod at
`tests/fixtures/skeleton_mod/`:

```
rimtrans translate --mod-path tests/fixtures/skeleton_mod --output ./out
rimtrans build --output ./out
```

produces `./out/RimTransWalkingSkeletonRU/{About/About.xml,Languages/Russian/Keyed/test.skeletonmod.xml}`,
matching Epic #71's acceptance criteria. Also covered by an automated
integration test (`tests/test_pipeline.py`) and CLI-level tests
(`tests/test_cli.py`).

## What's explicitly not done here (known limitations)

- **#74 — Real RimWorld 1.6 install verification: BLOCKED, not attempted.**
  This session runs in an isolated cloud container with no RimWorld
  installation and no display — there is no way to install the generated
  mod in a real game instance or observe in-game rendering from here. The
  pipeline's *output* is structurally validated (well-formed XML,
  `loadAfter`/`modDependencies` correct, `<!-- EN: ... -->` comments
  present), but the actual "load the game, see Russian text" step from
  issue #74's acceptance criteria requires a human with a RimWorld 1.6
  install to run the two commands above, install
  `RimTransWalkingSkeletonRU` alongside the fixture (or a real) mod, and
  document the result on that issue. Issue #74 is left open, not closed,
  pending that manual step.
- **#75 — Swap in TranslateGemma via Ollama: BLOCKED, not attempted.**
  Depends on #33/#36 (a live Ollama server + GPU), neither of which exists
  in this environment. Left open pending that infrastructure and a
  configuration-only change per its own scope (no new provider code).

## Known scope simplifications (documented, not silently assumed)

- `scan_mod` resolves only "mod root" or "`<version>/`" content roots — no
  `LoadFolders.xml` parsing (full scope stays with issue #19).
- `generate_keyed_tree` filters on `validation_status == PASSED` only; the
  full-scope `review_status` gate (issue #52) is a no-op here since no
  review pipeline exists yet in the walking skeleton.
- `validate()` runs the placeholder-preservation check only; the remaining
  Epic #6 gates (RulePack symbols, rich text, escapes, XML validity, key
  integrity) are not implemented here (issue #48's full orchestration).
