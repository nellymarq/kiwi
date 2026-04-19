"""Tests for progress tracking."""

from memory import client_manager
from memory.progress import KNOWN_METRICS, ProgressTracker


def test_record_and_get(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("weight", 77.5)
    history = pt.get_history("weight")
    assert len(history) == 1
    assert history[0]["value"] == 77.5
    assert history[0]["unit"] == "kg"


def test_training_load_in_known_metrics(clean_client):
    """Tier 34: training_load registered with AU units."""
    assert KNOWN_METRICS["training_load"] == "AU"


def test_record_training_load(clean_client):
    """Standard record() works for training_load with auto-unit."""
    pt = ProgressTracker(client=clean_client)
    pt.record("training_load", 450.0)
    latest = pt.get_latest("training_load")
    assert latest is not None
    assert latest["value"] == 450.0
    assert latest["unit"] == "AU"


def test_record_with_note(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("ferritin", 45.0, note="post-supplementation retest")
    history = pt.get_history("ferritin")
    assert history[0]["note"] == "post-supplementation retest"


def test_auto_unit_from_known_metrics(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("testosterone", 620.0)
    latest = pt.get_latest("testosterone")
    assert latest["unit"] == "ng/dL"


def test_custom_metric(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("grip_strength", 55.0, unit="kg")
    latest = pt.get_latest("grip_strength")
    assert latest["value"] == 55.0
    assert latest["unit"] == "kg"


def test_get_history_multiple(clean_client):
    pt = ProgressTracker(client=clean_client)
    for val in [78.0, 77.5, 77.0, 76.5]:
        pt.record("weight", val)
    history = pt.get_history("weight")
    assert len(history) == 4
    assert history[0]["value"] == 78.0
    assert history[-1]["value"] == 76.5


def test_get_latest(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("weight", 80.0)
    pt.record("weight", 79.0)
    latest = pt.get_latest("weight")
    assert latest["value"] == 79.0


def test_get_latest_no_data(clean_client):
    pt = ProgressTracker(client=clean_client)
    assert pt.get_latest("nonexistent") is None


def test_get_all_metrics(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("weight", 80.0)
    pt.record("ferritin", 30.0)
    pt.record("weight", 79.5)
    metrics = pt.get_all_metrics()
    assert "weight" in metrics
    assert "ferritin" in metrics


def test_format_trend(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("weight", 80.0)
    pt.record("weight", 79.0)
    pt.record("weight", 78.0)
    output = pt.format_trend("weight")
    assert "Trend: weight" in output
    assert "80.0" in output
    assert "78.0" in output
    assert "Change:" in output
    assert "↓" in output


def test_format_trend_no_data(clean_client):
    pt = ProgressTracker(client=clean_client)
    output = pt.format_trend("missing")
    assert "No data" in output


def test_format_dashboard(clean_client):
    pt = ProgressTracker(client=clean_client)
    pt.record("weight", 77.0)
    pt.record("ferritin", 45.0)
    output = pt.format_dashboard()
    assert "weight" in output
    assert "ferritin" in output
    assert "77.0" in output
    assert "45.0" in output


def test_format_dashboard_empty(clean_client):
    pt = ProgressTracker(client=clean_client)
    output = pt.format_dashboard()
    assert "No metrics" in output


def test_per_client_isolation(clean_client):
    client_manager.create_client("other_athlete", "")
    pt_a = ProgressTracker(client=clean_client)
    pt_a.record("weight", 80.0)

    pt_b = ProgressTracker(client="other_athlete")
    assert pt_b.get_history("weight") == []


def test_known_metrics_includes_common():
    assert "weight" in KNOWN_METRICS
    assert "ferritin" in KNOWN_METRICS
    assert "testosterone" in KNOWN_METRICS
    assert "squat_1rm" in KNOWN_METRICS
    assert "sleep_hours" in KNOWN_METRICS
