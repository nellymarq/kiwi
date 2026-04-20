"""Tier 57 — smoke tests for handlers/planning.py (async)."""
import asyncio
from unittest.mock import MagicMock


def test_planning_handlers_importable():
    from handlers.planning import handle_meal_plan, handle_training_plan
    assert asyncio.iscoroutinefunction(handle_meal_plan)
    assert asyncio.iscoroutinefunction(handle_training_plan)


def test_handle_meal_plan_missing_profile_returns_early():
    """When profile is missing required fields, prints hint and returns without calling agent."""
    from handlers.planning import handle_meal_plan
    kiwi = MagicMock()
    kiwi.profile.get.return_value = None  # all required fields missing
    asyncio.run(handle_meal_plan(kiwi, "/meal_plan 3", "/meal_plan 3"))
    # Should print the "missing fields" hint but NOT call the agent
    assert kiwi.console.print.called
    kiwi.meal_plan_agent.run.assert_not_called()
