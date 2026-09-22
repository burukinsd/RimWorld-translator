# Engineering Policy

This file is read automatically at the start of every Claude Code session in
this repository. The rules below are a **standing engineering policy**, not
task-specific instructions — apply them to every piece of development, bug
fix, test, refactor, and code review from here on, not just the task that
introduced them.

Before starting any non-trivial task, explicitly check: *how should these
rules shape the plan and approach for this specific task?* Don't just recall
them — apply them to scope, architecture, testing strategy, review, and
context usage each time.

## 1. Code

- Follow the project's existing code style and architecture.
- Prefer simple, readable, testable code.
- Don't add abstractions, dependencies, or architectural layers without a
  concrete need.
- Don't duplicate existing functionality.
- Don't mix several independent changes into one task.

## 2. Development loop

For every non-trivial change, follow this cycle:

```
UNDERSTAND → PLAN → IMPLEMENT → TARGETED TEST → INSPECT DIFF
→ SELF-REVIEW → INTEGRATION VALIDATION → DOCUMENT
```

Don't make large, unverified changes in one step.

## 3. Tests

- Tests are part of the implementation, not a follow-up step.
- For every change, identify what behavior could break.
- Add regression tests for every bug fixed.
- Cover the happy path, error paths, and important boundary cases.
- Prefer fast, deterministic tests.
- Test behavior, not internal implementation, wherever possible.
- Don't run the entire test suite after every small change when targeted
  tests give enough confidence.
- Before finishing a non-trivial task, run the broader validation that's
  actually needed (e.g. full suite, build, lint) — don't skip it.

## 4. Code review

Before finishing any non-trivial task, do a self-review as an independent
reviewer would. Check:

- correctness
- edge cases
- backwards compatibility
- architecture
- duplication
- complexity
- performance
- tests
- readability
- accidental/unrelated changes
- whether documentation needs updating

A task is not done just because the code runs or tests pass.

## 5. Context and token economy (architectural requirement)

Efficient use of context, tokens, and compute is part of this project's
architecture — not just a "don't waste tokens" guideline. Design the
development process itself to minimize repeated work:

- Record durable decisions in documentation, ADRs, and GitHub Issues.
- Don't make future tasks re-investigate decisions already made.
- Treat existing docs and issues as the source of truth.
- Don't re-read entire files when only a small fragment is needed.
- Use targeted search instead of scanning the whole repository.
- Don't load large logs into context when the relevant part can be
  filtered out first.
- Don't repeat information that hasn't changed.
- Persist the results of expensive investigation somewhere reusable.
- Implement incrementally; verify each significant step before moving on.
- Don't pre-research information only needed at a later stage.
- Don't build large speculative plans for small tasks.

If a process routinely requires a large amount of context, treat that as a
potential architectural problem with the *process*, not just a token-usage
issue — and consider fixing it via documentation, automation, caching,
tests, scripts, smaller tasks, better tooling, or repo restructuring.

The goal is not "use fewer tokens" — it's reducing how much re-thinking,
re-reading, and context-passing is needed to reach the same result.

## 6. Research order

Consult sources in this order, and don't redo research that's already
reliably established in the project:

1. existing code
2. tests
3. project documentation
4. GitHub Issues / ADRs
5. dependency documentation
6. external authoritative sources

## 7. Scope

Always stick to the minimum necessary scope. If an unrelated problem is
found:

- don't fix it automatically
- note it (and open a separate issue if warranted)
- don't turn a small task into unplanned refactoring

## 8. Git

- Keep changes logically separated.
- Don't touch unrelated user work.
- Don't mix feature changes, refactoring, formatting, and dependency
  updates unless necessary.

## 9. Documentation

If a decision matters for future development, record it in a durable
project artifact (docs, ADR, issue) — don't rely on conversation memory.
The repository itself should progressively become the primary source of
project context.

## 10. Handling uncertainty

Don't guess. Distinguish between:

- known
- inferred
- unverified
- blocked

Do the minimum research needed to resolve *significant* uncertainty — don't
spend a lot of context on a question that barely affects the outcome.

## 11. Definition of Done

A task is done only when:

- the requirement is met
- scope stayed controlled
- necessary tests were written and pass
- a self-review was done
- the diff was inspected
- important decisions are documented
- there are no accidental changes
- known limitations are recorded

If something wasn't verified, say so explicitly rather than implying it was.

## Conflicts with existing process

If the existing project process conflicts with these rules, don't silently
follow either one — flag the conflict explicitly and propose how to resolve
it.
