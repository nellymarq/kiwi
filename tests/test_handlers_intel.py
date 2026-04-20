"""Tier 62 — smoke tests for handlers/intel.py."""
import asyncio


def test_intel_handlers_importable():
    from handlers.intel import (
        handle_brief,
        handle_capabilities,
        handle_freshness,
        handle_frontiers,
        handle_gaps,
        handle_macros,
        handle_retest_due,
        handle_template,
        handle_timing,
        handle_weekly_report,
    )
    assert asyncio.iscoroutinefunction(handle_brief)
    for h in (handle_template, handle_frontiers, handle_freshness, handle_macros,
              handle_weekly_report, handle_capabilities, handle_timing, handle_retest_due, handle_gaps):
        assert callable(h)
