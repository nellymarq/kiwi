"""Tier 52 — smoke tests for handlers/training_load.py."""
from unittest.mock import MagicMock


def test_training_load_handlers_importable():
    from handlers.training_load import handle_blocks, handle_load, handle_prilepin, handle_session
    for h in (handle_session, handle_load, handle_blocks, handle_prilepin):
        assert callable(h)


def test_handle_load_no_sessions_prints_hint():
    from handlers.training_load import handle_load
    kiwi = MagicMock()
    kiwi._pending_sessions = []
    handle_load(kiwi, "/load", "/load")
    assert kiwi.console.print.called


def test_handle_prilepin_invalid_prints_usage():
    from handlers.training_load import handle_prilepin
    kiwi = MagicMock()
    handle_prilepin(kiwi, "/prilepin", "/prilepin")
    assert kiwi.console.print.called
