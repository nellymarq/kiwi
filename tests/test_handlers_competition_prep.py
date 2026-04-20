"""Tier 58 — smoke tests for handlers/competition_prep.py (async)."""
import asyncio


def test_competition_prep_handler_importable():
    from handlers.competition_prep import handle_competition_prep
    assert asyncio.iscoroutinefunction(handle_competition_prep)
