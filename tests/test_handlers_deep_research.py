"""Tier 63 — smoke tests for handlers/deep_research.py."""
import asyncio


def test_deep_research_handlers_importable():
    from handlers.deep_research import (
        handle_autoquality,
        handle_effect,
        handle_grade,
        handle_n_of_1,
        handle_quality,
        handle_readpdf,
        handle_recommend,
        handle_review,
        handle_synthesize,
    )
    for h in (handle_synthesize, handle_review, handle_n_of_1, handle_recommend):
        assert asyncio.iscoroutinefunction(h)
    for h in (handle_effect, handle_readpdf, handle_autoquality, handle_quality, handle_grade):
        assert callable(h)
