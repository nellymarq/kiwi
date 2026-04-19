"""Tests for intervention tracking with outcome correlation."""

from memory import client_manager
from memory.interventions import InterventionTracker
from memory.progress import ProgressTracker


def test_start_intervention(clean_client):
    it = InterventionTracker(client=clean_client)
    entry = it.start("iron", dose="36mg/d", target_metric="ferritin", note="Low ferritin protocol")
    assert entry["name"] == "iron"
    assert entry["dose"] == "36mg/d"
    assert entry["target_metric"] == "ferritin"
    assert entry["status"] == "active"


def test_list_active(clean_client):
    it = InterventionTracker(client=clean_client)
    it.start("iron", dose="36mg/d")
    it.start("vitamin_c", dose="500mg/d")
    active = it.list_active()
    assert len(active) == 2


def test_stop_intervention(clean_client):
    it = InterventionTracker(client=clean_client)
    it.start("creatine", dose="5g/d")
    assert it.stop("creatine", reason="Pre-weigh-in cessation")
    active = it.list_active()
    assert len(active) == 0
    all_entries = it.list_all()
    assert all_entries[0]["status"] == "stopped"
    assert all_entries[0]["stop_reason"] == "Pre-weigh-in cessation"


def test_stop_nonexistent(clean_client):
    it = InterventionTracker(client=clean_client)
    assert not it.stop("ghost_supplement")


def test_persistence(clean_client):
    it1 = InterventionTracker(client=clean_client)
    it1.start("iron")
    it1.start("vitamin_d")

    it2 = InterventionTracker(client=clean_client)
    assert len(it2.list_active()) == 2


def test_check_outcome_no_target(clean_client):
    it = InterventionTracker(client=clean_client)
    it.start("creatine")
    result = it.check_outcome("creatine")
    assert "No target metric" in result.get("message", "")


def test_check_outcome_no_data(clean_client):
    it = InterventionTracker(client=clean_client)
    it.start("iron", target_metric="ferritin")
    result = it.check_outcome("iron")
    assert "No progress data" in result.get("message", "")


def test_check_outcome_with_data(clean_client):
    # Record baseline biomarkers
    pt = ProgressTracker(client=clean_client)
    pt.record("ferritin", 15.0)
    pt.record("ferritin", 18.0)

    # Start intervention
    it = InterventionTracker(client=clean_client)
    it.start("iron", dose="36mg/d", target_metric="ferritin")

    # Record post-intervention biomarkers
    pt.record("ferritin", 25.0)
    pt.record("ferritin", 35.0)

    result = it.check_outcome("iron")
    assert "baseline_avg" in result or "post_avg" in result


def test_check_outcome_not_found(clean_client):
    it = InterventionTracker(client=clean_client)
    result = it.check_outcome("ghost")
    assert "error" in result


def test_format_active_empty(clean_client):
    it = InterventionTracker(client=clean_client)
    output = it.format_active()
    assert "No active" in output


def test_format_active_with_entries(clean_client):
    it = InterventionTracker(client=clean_client)
    it.start("iron", dose="36mg/d", target_metric="ferritin")
    output = it.format_active()
    assert "iron" in output
    assert "36mg/d" in output
    assert "ferritin" in output


def test_format_outcome(clean_client):
    it = InterventionTracker(client=clean_client)
    result = {"intervention": "iron", "message": "No data"}
    output = it.format_outcome(result)
    assert "No data" in output


def test_per_client_isolation(clean_client):
    client_manager.create_client("other", "")
    it_a = InterventionTracker(client=clean_client)
    it_a.start("iron")

    it_b = InterventionTracker(client="other")
    assert len(it_b.list_active()) == 0
