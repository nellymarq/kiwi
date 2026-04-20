"""Tier 48 — smoke tests for handlers/recovery.py."""
from unittest.mock import MagicMock


def test_recovery_handlers_importable():
    from handlers.recovery import (
        handle_deload,
        handle_doms,
        handle_mps,
        handle_readiness,
        handle_recover,
        handle_supercomp,
    )
    for h in (handle_readiness, handle_doms, handle_supercomp, handle_deload, handle_recover, handle_mps):
        assert callable(h)


def test_handle_readiness_no_args_prints_usage():
    from handlers.recovery import handle_readiness
    kiwi = MagicMock()
    handle_readiness(kiwi, "/readiness", "/readiness")
    assert kiwi.console.print.called


def test_handle_mps_default_weight_from_profile():
    from handlers.recovery import handle_mps
    kiwi = MagicMock()
    kiwi.profile.data.get.return_value = 75.0
    handle_mps(kiwi, "/mps", "/mps")
    assert kiwi.console.print.called
