"""Tier 46 — smoke tests for handlers/body_composition.py."""
from unittest.mock import MagicMock


def test_body_comp_handlers_importable():
    from handlers.body_composition import (
        handle_bodyfat,
        handle_ea,
        handle_ffmi,
        handle_skinfold,
        handle_weightplan,
    )
    for h in (handle_skinfold, handle_bodyfat, handle_ffmi, handle_ea, handle_weightplan):
        assert callable(h)


def test_handle_skinfold_no_args_prints_usage():
    from handlers.body_composition import handle_skinfold
    kiwi = MagicMock()
    handle_skinfold(kiwi, "/skinfold ", "/skinfold ")
    assert kiwi.console.print.called


def test_handle_ea_no_args_prints_usage():
    from handlers.body_composition import handle_ea
    kiwi = MagicMock()
    handle_ea(kiwi, "/ea ", "/ea ")
    assert kiwi.console.print.called
