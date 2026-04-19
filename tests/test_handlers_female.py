"""Tier 44 — smoke tests for handlers/female.py."""
from unittest.mock import MagicMock


def test_female_handlers_importable():
    from handlers.female import handle_cycle, handle_iron, handle_postpartum, handle_reds
    assert callable(handle_cycle)
    assert callable(handle_reds)
    assert callable(handle_iron)
    assert callable(handle_postpartum)


def test_handle_cycle_no_args_lists_phases():
    from handlers.female import handle_cycle
    kiwi = MagicMock()
    handle_cycle(kiwi, "/cycle", "/cycle")
    assert kiwi.console.print.called


def test_handle_reds_no_arg_prints_usage():
    from handlers.female import handle_reds
    kiwi = MagicMock()
    handle_reds(kiwi, "/reds", "/reds")
    assert kiwi.console.print.called
