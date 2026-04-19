"""Tier 42 — smoke tests for handlers/mental.py."""
from unittest.mock import MagicMock


def test_mental_handlers_importable():
    from handlers.mental import handle_anxiety, handle_burnout, handle_visualize
    assert callable(handle_anxiety)
    assert callable(handle_burnout)
    assert callable(handle_visualize)


def test_handle_anxiety_invalid_args_prints_usage():
    from handlers.mental import handle_anxiety
    kiwi = MagicMock()
    handle_anxiety(kiwi, "/anxiety", "/anxiety")  # no args
    assert kiwi.console.print.called


def test_handle_visualize_no_arg_lists_protocols():
    from handlers.mental import handle_visualize
    kiwi = MagicMock()
    handle_visualize(kiwi, "/visualize", "/visualize")
    assert kiwi.console.print.called
