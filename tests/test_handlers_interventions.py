"""Tier 54 — smoke tests for handlers/interventions.py."""
from unittest.mock import MagicMock


def test_intervention_handler_importable():
    from handlers.interventions import handle_intervention
    assert callable(handle_intervention)


def test_handle_intervention_no_args_prints_usage():
    from handlers.interventions import handle_intervention
    kiwi = MagicMock()
    handle_intervention(kiwi, "/intervention ", "/intervention ")
    assert kiwi.console.print.called


def test_handle_intervention_unknown_subcommand_prints_help():
    from handlers.interventions import handle_intervention
    kiwi = MagicMock()
    handle_intervention(kiwi, "/intervention bogus", "/intervention bogus")
    assert kiwi.console.print.called
