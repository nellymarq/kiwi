"""Tier 41 pilot — smoke tests for handlers/injury.py module.

Proves the import path works and handler signatures are callable with
a mock Kiwi. Does not exercise full behavior — that's covered by
tests/test_injury_prevention.py for the underlying tools.
"""
from unittest.mock import MagicMock


def test_injury_handlers_importable():
    """All 5 Injury handlers should be importable as module-level callables."""
    from handlers.injury import (
        handle_acwr,
        handle_fms,
        handle_overuse,
        handle_prevent,
        handle_return_to_sport,
    )
    assert callable(handle_acwr)
    assert callable(handle_fms)
    assert callable(handle_overuse)
    assert callable(handle_prevent)
    assert callable(handle_return_to_sport)


def test_handle_acwr_no_args_no_history_prints_usage():
    """/acwr with no args AND no tracked history → usage message via kiwi.console."""
    from handlers.injury import handle_acwr

    kiwi = MagicMock()
    kiwi.progress.get_history.return_value = []
    handle_acwr(kiwi, "/acwr", "/acwr")
    assert kiwi.console.print.called


def test_handle_prevent_no_arg_lists_protocols():
    """Bare /prevent → lists all protocols via kiwi.console."""
    from handlers.injury import handle_prevent

    kiwi = MagicMock()
    handle_prevent(kiwi, "/prevent", "/prevent")
    assert kiwi.console.print.called
