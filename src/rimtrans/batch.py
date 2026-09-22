"""Convention for reporting a partial failure without aborting a batch.

Any component that processes a collection of independent items (mods,
extracted strings, provider calls) should route through `run_batch` rather
than a bare loop, so one item's `RecoverableError` never takes down the
rest of the batch. A `FatalError` (or any other unexpected exception) is
not caught here — it propagates immediately, since by definition the run
cannot usefully continue.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

from rimtrans.errors import RecoverableError

T = TypeVar("T")


class SupportsWarning(Protocol):
    """Minimal logger shape `run_batch` needs — matches both `logging.Logger`
    and `logging.LoggerAdapter` structurally, without requiring either."""

    def warning(self, msg: str, *args: object) -> None: ...
R = TypeVar("R")


@dataclass
class BatchItemFailure(Generic[T]):
    """One item's `RecoverableError`, paired with the item that caused it."""

    item: T
    error: RecoverableError


@dataclass
class BatchResult(Generic[T, R]):
    """Outcome of `run_batch`: whatever succeeded, and whatever didn't."""

    successes: list[R] = field(default_factory=list)
    failures: list[BatchItemFailure[T]] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return not self.failures


def run_batch(
    items: Iterable[T],
    fn: Callable[[T], R],
    *,
    logger: SupportsWarning | None = None,
) -> BatchResult[T, R]:
    """Apply `fn` to each item, isolating `RecoverableError` per item.

    Any exception other than `RecoverableError` (including `FatalError`)
    propagates immediately and aborts the batch, consistent with
    `docs/adr/0002-logging-and-error-conventions.md`.
    """
    result: BatchResult[T, R] = BatchResult()
    for item in items:
        try:
            result.successes.append(fn(item))
        except RecoverableError as exc:
            if logger is not None:
                logger.warning("batch item failed: %s", exc)
            result.failures.append(BatchItemFailure(item=item, error=exc))
    return result
