"""Tier 51 — smoke tests for handlers/food.py + handlers/supplements.py.

First tier with async handlers (/check, /interact).
"""
import asyncio
from unittest.mock import MagicMock


def test_food_handlers_importable():
    from handlers.food import handle_compare, handle_food
    assert callable(handle_food)
    assert callable(handle_compare)


def test_supplement_handlers_importable():
    from handlers.supplements import (
        handle_check,
        handle_interact,
        handle_supp,
        handle_supplist,
    )
    assert callable(handle_supplist)
    assert callable(handle_supp)
    # async handlers are callables too (coroutine functions)
    assert asyncio.iscoroutinefunction(handle_check)
    assert asyncio.iscoroutinefunction(handle_interact)


def test_handle_food_no_name_prints_usage():
    from handlers.food import handle_food
    kiwi = MagicMock()
    handle_food(kiwi, "/food ", "/food ")
    assert kiwi.console.print.called


def test_handle_supp_unknown_prints_yellow_warning():
    from handlers.supplements import handle_supp
    kiwi = MagicMock()
    handle_supp(kiwi, "/supp zzznonexistent", "/supp zzznonexistent")
    assert kiwi.console.print.called


def test_handle_check_empty_prints_usage():
    """Async handler must run via asyncio."""
    from handlers.supplements import handle_check
    kiwi = MagicMock()
    asyncio.run(handle_check(kiwi, "/check ", "/check "))
    assert kiwi.console.print.called
