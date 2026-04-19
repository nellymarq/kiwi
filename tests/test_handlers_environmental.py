"""Tier 43 — smoke tests for handlers/environmental.py."""
from unittest.mock import MagicMock


def test_environmental_handlers_importable():
    from handlers.environmental import (
        handle_airquality,
        handle_altitude,
        handle_cold,
        handle_heat,
        handle_jetlag,
    )
    assert callable(handle_altitude)
    assert callable(handle_heat)
    assert callable(handle_cold)
    assert callable(handle_airquality)
    assert callable(handle_jetlag)


def test_handle_altitude_no_args_prints_usage():
    from handlers.environmental import handle_altitude
    kiwi = MagicMock()
    handle_altitude(kiwi, "/altitude", "/altitude")
    assert kiwi.console.print.called


def test_handle_jetlag_invalid_prints_usage():
    from handlers.environmental import handle_jetlag
    kiwi = MagicMock()
    handle_jetlag(kiwi, "/jetlag", "/jetlag")
    assert kiwi.console.print.called
