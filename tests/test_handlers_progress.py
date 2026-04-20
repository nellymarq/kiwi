"""Tier 53 — smoke tests for handlers/progress.py."""
from unittest.mock import MagicMock


def test_progress_handlers_importable():
    from handlers.progress import handle_dashboard, handle_team, handle_track, handle_trends_with_metric
    for h in (handle_track, handle_trends_with_metric, handle_dashboard, handle_team):
        assert callable(h)


def test_handle_track_no_args_prints_usage():
    from handlers.progress import handle_track
    kiwi = MagicMock()
    handle_track(kiwi, "/track ", "/track ")
    assert kiwi.console.print.called


def test_handle_dashboard_prints_report():
    from handlers.progress import handle_dashboard
    kiwi = MagicMock()
    kiwi.progress.format_dashboard.return_value = "fake dashboard"
    handle_dashboard(kiwi, "/dashboard", "/dashboard")
    assert kiwi.console.print.called
