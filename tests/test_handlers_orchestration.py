"""Tier 60 — smoke tests for handlers/orchestration.py."""
from unittest.mock import MagicMock


def test_orchestration_handlers_importable():
    from handlers.orchestration import handle_digest, handle_unwatch, handle_watch, handle_watched
    for h in (handle_watch, handle_unwatch, handle_watched, handle_digest):
        assert callable(h)


def test_handle_watched_empty_prints_hint():
    from handlers.orchestration import handle_watched
    kiwi = MagicMock()
    kiwi.watch_list.list_topics.return_value = []
    handle_watched(kiwi, "/watched", "/watched")
    assert kiwi.console.print.called


def test_handle_digest_no_topics_prints_hint():
    from handlers.orchestration import handle_digest
    kiwi = MagicMock()
    kiwi.watch_list.list_topics.return_value = []
    handle_digest(kiwi, "/digest", "/digest")
    assert kiwi.console.print.called
