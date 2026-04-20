"""Tier 49 — smoke tests for handlers/hydration.py."""
from unittest.mock import MagicMock


def test_hydration_handlers_importable():
    from handlers.hydration import (
        handle_hyponatremia,
        handle_prehydrate,
        handle_rehydrate,
        handle_sweat,
        handle_sweatest,
        handle_urine,
    )
    for h in (handle_sweat, handle_sweatest, handle_rehydrate, handle_urine, handle_hyponatremia, handle_prehydrate):
        assert callable(h)


def test_handle_urine_no_args_prints_usage():
    from handlers.hydration import handle_urine
    kiwi = MagicMock()
    handle_urine(kiwi, "/urine ", "/urine ")
    assert kiwi.console.print.called


def test_handle_sweat_no_args_prints_usage():
    from handlers.hydration import handle_sweat
    kiwi = MagicMock()
    handle_sweat(kiwi, "/sweat ", "/sweat ")
    assert kiwi.console.print.called
