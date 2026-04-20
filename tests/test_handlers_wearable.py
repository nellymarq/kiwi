"""Tier 59 — smoke tests for handlers/wearable.py."""
from unittest.mock import MagicMock


def test_wearable_handlers_importable():
    from handlers.wearable import handle_import_labs, handle_import_wearable, handle_oura
    assert callable(handle_oura)
    assert callable(handle_import_wearable)
    assert callable(handle_import_labs)


def test_handle_oura_no_token_prints_hint(monkeypatch):
    from handlers.wearable import handle_oura
    monkeypatch.delenv("OURA_TOKEN", raising=False)
    kiwi = MagicMock()
    kiwi.config.get.return_value = ""
    handle_oura(kiwi, "/oura sync", "/oura sync")
    assert kiwi.console.print.called


def test_handle_import_wearable_no_path_prints_usage():
    from handlers.wearable import handle_import_wearable
    kiwi = MagicMock()
    handle_import_wearable(kiwi, "/import_wearable ", "/import_wearable ")
    assert kiwi.console.print.called
