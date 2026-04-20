"""Tier 61 — smoke tests for handlers/optimization.py (async)."""
import asyncio


def test_optimization_handlers_importable():
    from handlers.optimization import handle_optimize_stack, handle_risk_screen, handle_suggest_research
    assert asyncio.iscoroutinefunction(handle_optimize_stack)
    assert asyncio.iscoroutinefunction(handle_risk_screen)
    assert asyncio.iscoroutinefunction(handle_suggest_research)
