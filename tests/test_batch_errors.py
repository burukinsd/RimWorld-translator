"""A recoverable error in one item must not abort the rest of the batch.

This is the scenario issue #15's acceptance criteria calls for: "a sample
recoverable-error scenario ... is demonstrated not to abort a multi-item
batch operation."
"""

from __future__ import annotations

import pytest

from rimtrans.batch import run_batch
from rimtrans.errors import FatalError, RecoverableError


class MalformedItemError(RecoverableError):
    """Stand-in for a real per-item error, e.g. one malformed XML file."""


def test_recoverable_error_does_not_abort_remaining_items() -> None:
    items = [1, 2, 3, 4, 5]

    def process(item: int) -> int:
        if item == 3:
            raise MalformedItemError(f"item {item} is malformed")
        return item * 10

    result = run_batch(items, process)

    assert result.successes == [10, 20, 40, 50]
    assert len(result.failures) == 1
    assert result.failures[0].item == 3
    assert isinstance(result.failures[0].error, MalformedItemError)
    assert not result.all_succeeded


def test_all_succeed_when_nothing_fails() -> None:
    result = run_batch([1, 2, 3], lambda x: x + 1)

    assert result.successes == [2, 3, 4]
    assert result.failures == []
    assert result.all_succeeded


def test_fatal_error_propagates_and_aborts_the_batch() -> None:
    def process(item: int) -> int:
        if item == 2:
            raise FatalError("cannot continue")
        return item

    with pytest.raises(FatalError):
        run_batch([1, 2, 3], process)


def test_logger_receives_a_warning_for_each_failure() -> None:
    calls: list[str] = []

    class RecordingLogger:
        def warning(self, msg: str, *args: object) -> None:
            calls.append(msg % args if args else msg)

    def process(item: int) -> int:
        if item == 1:
            raise MalformedItemError("boom")
        return item

    run_batch([1, 2], process, logger=RecordingLogger())

    assert len(calls) == 1
    assert "boom" in calls[0]
