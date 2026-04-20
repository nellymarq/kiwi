"""Tier 56 — smoke tests for handlers/literature.py."""
from unittest.mock import MagicMock


def test_literature_handlers_importable():
    from handlers.literature import (
        handle_citedby,
        handle_fulltext,
        handle_openalex,
        handle_pubmed,
        handle_tldr,
        handle_trials,
    )
    for h in (handle_pubmed, handle_fulltext, handle_tldr, handle_trials, handle_citedby, handle_openalex):
        assert callable(h)


def test_handle_pubmed_disabled_prints_hint():
    from handlers.literature import handle_pubmed
    kiwi = MagicMock()
    kiwi.pubmed = None
    handle_pubmed(kiwi, "/pubmed creatine", "/pubmed creatine")
    assert kiwi.console.print.called


def test_handle_fulltext_disabled_prints_hint():
    from handlers.literature import handle_fulltext
    kiwi = MagicMock()
    kiwi.unpaywall = None
    handle_fulltext(kiwi, "/fulltext 10.1/test", "/fulltext 10.1/test")
    assert kiwi.console.print.called
