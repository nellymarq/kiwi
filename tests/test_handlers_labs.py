"""Tier 50 — smoke tests for handlers/labs.py."""
from unittest.mock import MagicMock


def test_labs_handlers_importable():
    from handlers.labs import handle_biomarker, handle_labs
    assert callable(handle_labs)
    assert callable(handle_biomarker)


def test_handle_labs_no_args_prints_usage():
    from handlers.labs import handle_labs
    kiwi = MagicMock()
    handle_labs(kiwi, "/labs ", "/labs ")
    assert kiwi.console.print.called


def test_handle_biomarker_no_args_prints_usage():
    from handlers.labs import handle_biomarker
    kiwi = MagicMock()
    handle_biomarker(kiwi, "/biomarker ", "/biomarker ")
    assert kiwi.console.print.called
