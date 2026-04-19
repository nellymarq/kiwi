"""Tier 45 — smoke tests for handlers/training_zones.py."""
from unittest.mock import MagicMock


def test_training_zones_handlers_importable():
    from handlers.training_zones import (
        handle_distribution,
        handle_hrmax,
        handle_hrzones,
        handle_pacezones,
        handle_powerzones,
        handle_vo2max,
    )
    for h in (handle_hrzones, handle_powerzones, handle_pacezones, handle_vo2max, handle_hrmax, handle_distribution):
        assert callable(h)


def test_handle_hrzones_no_args_prints_usage():
    from handlers.training_zones import handle_hrzones
    kiwi = MagicMock()
    handle_hrzones(kiwi, "/hrzones ", "/hrzones ")
    assert kiwi.console.print.called


def test_handle_hrmax_no_args_prints_usage():
    from handlers.training_zones import handle_hrmax
    kiwi = MagicMock()
    handle_hrmax(kiwi, "/hrmax ", "/hrmax ")
    assert kiwi.console.print.called
