"""Tier 55 — smoke tests for handlers/sports.py (async)."""
import asyncio


def test_assess_handler_importable():
    from handlers.sports import handle_assess
    assert asyncio.iscoroutinefunction(handle_assess)
