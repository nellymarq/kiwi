"""Tier 47 — smoke tests for handlers/sleep.py."""
from unittest.mock import MagicMock


def test_sleep_handlers_importable():
    from handlers.sleep import (
        handle_bedtime,
        handle_caffeine,
        handle_chronotype,
        handle_hormones,
        handle_sleep,
        handle_sleepdebt,
    )
    for h in (handle_sleep, handle_chronotype, handle_caffeine, handle_sleepdebt, handle_hormones, handle_bedtime):
        assert callable(h)


def test_handle_hormones_prints_report():
    from handlers.sleep import handle_hormones
    kiwi = MagicMock()
    handle_hormones(kiwi, "/hormones", "/hormones")
    assert kiwi.console.print.called


def test_handle_caffeine_no_args_prints_usage():
    from handlers.sleep import handle_caffeine
    kiwi = MagicMock()
    handle_caffeine(kiwi, "/caffeine ", "/caffeine ")
    assert kiwi.console.print.called
