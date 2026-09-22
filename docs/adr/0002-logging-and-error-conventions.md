# ADR 0002: Logging and error-handling conventions

- Status: Accepted
- Related: Epic #1 (Architecture & Foundation), issue #15

## Context

The pipeline processes tens of thousands of strings across ~180 mods
(`ARCHITECTURE.md` §2, Epic #11). A failure in one mod's extraction or one
provider call must never abort a whole run — but a genuinely fatal problem
(bad config, an unreachable required provider) must stop the run rather
than silently produce a broken/incomplete result. This ADR fixes the
convention every later Epic's components follow.

## Decision

### Error hierarchy (`rimtrans/errors.py`)

```
RimTransError               # base class for all rimtrans errors
├─ FatalError                # run-level: abort the current command
│   └─ ConfigError            # missing/malformed/invalid config
└─ RecoverableError           # per-item: record it, keep going
```

Components define their own subclasses as needed (e.g. an Epic #2
`MalformedXmlError(RecoverableError)`, an Epic #4
`ProviderUnavailableError(FatalError)`) rather than raising the base
classes directly, so callers can `except` a specific error type without
matching everything.

**Rule of thumb:** if the pipeline can meaningfully process the *next*
item after this failure, it's `RecoverableError`. If it can't (or
shouldn't try to), it's `FatalError`.

### Partial-failure convention (`rimtrans/batch.py`)

Any component iterating over independent items routes through
`run_batch(items, fn)` instead of a bare loop:

```python
from rimtrans.batch import run_batch

result = run_batch(mod_files, extract_one_file, logger=logger)
# result.successes: list of successful outputs
# result.failures: list of BatchItemFailure(item, error) — one per
#                   RecoverableError, item preserved for reporting
```

`RecoverableError` raised inside `fn` is caught, logged as a warning, and
recorded in `result.failures`; processing continues with the next item.
Anything else (including `FatalError`) propagates immediately — the
run-level caller is expected to let it abort the command.

### Logging (`rimtrans/log.py`)

- **Levels:** `DEBUG` (verbose diagnostic detail, opt-in via CLI
  `--verbose`), `INFO` (normal progress — one line per mod/stage), `WARNING`
  (a `RecoverableError` was hit and skipped), `ERROR` (a `FatalError` is
  about to abort the run), `CRITICAL` reserved for unexpected crashes.
- **Two sinks:** a human-readable console stream (always on) and an
  optional structured JSON-lines file (`--log-file`, or wired up by a
  future Epic's command), so `rimtrans report` can query the file sink
  without parsing free text.
- **Structured fields:** `mod_id`, `domain`, `key`, `provider` are the
  fields every component is expected to attach when relevant, via
  `get_logger(component, **context)` or per-call `extra=`. This mirrors
  the Translation Memory columns in `ARCHITECTURE.md` §5, so a log line
  and its corresponding TM row can be correlated.
- **Attribution:** every error should be attributable to at least a
  component (via the logger name, `rimtrans.<component>`) and, where
  applicable, a specific mod/string (via the structured fields above) —
  this is what lets `rimtrans report` (Epic #9) surface failures
  meaningfully instead of a wall of undifferentiated log text.

## Example

`tests/test_batch_errors.py` demonstrates the required behavior: a batch
of five items where the third raises `RecoverableError` still processes
all five, returning four successes and one recorded failure — the
scenario this ADR's acceptance criteria (issue #15) calls for.
