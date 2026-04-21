"""Tests for cross-client team analytics."""

import json
import pytest
from pathlib import Path
from kiwi_core.memory import client_manager
from tools import team_analytics


@pytest.fixture
def populated_practice(tmp_path, monkeypatch):
    """Set up multiple clients with varied profile data."""
    monkeypatch.setattr(client_manager, "KIWI_DIR", tmp_path)
    monkeypatch.setattr(client_manager, "CLIENTS_DIR", tmp_path / "clients")
    monkeypatch.setattr(client_manager, "ACTIVE_CLIENT_FILE", tmp_path / "active_client.txt")
    monkeypatch.setattr(client_manager, "LEGACY_PROFILE", tmp_path / "profile.json")
    monkeypatch.setattr(client_manager, "LEGACY_MEMORY", tmp_path / "memory.json")
    monkeypatch.setattr(client_manager, "LEGACY_ARCHIVE", tmp_path / "episodic_archive.json")
    client_manager.ensure_setup()

    # Create 3 clients with different sports
    for name, sport, supps in [
        ("fighter_a", "MMA", ["creatine", "beta-alanine"]),
        ("fighter_b", "MMA", ["creatine", "omega_3"]),
        ("runner_a", "running", ["iron", "creatine"]),
    ]:
        client_manager.create_client(name, "")
        profile = {
            "weight_kg": 75.0,
            "height_cm": 175,
            "age": 28,
            "sex": "male",
            "activity_level": "very_active",
            "sport": sport,
            "current_supplements": supps,
        }
        profile_path = client_manager.profile_path(name)
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(json.dumps(profile))

    return tmp_path


def test_snapshot_clients(populated_practice):
    snapshots = team_analytics.snapshot_clients()
    names = {s.name for s in snapshots}
    assert "fighter_a" in names
    assert "fighter_b" in names
    assert "runner_a" in names
    # 'self' excluded by default
    assert "self" not in names


def test_snapshot_include_self(populated_practice):
    snapshots = team_analytics.snapshot_clients(include_self=True)
    names = {s.name for s in snapshots}
    assert "self" in names


def test_snapshot_profile_data(populated_practice):
    snapshots = team_analytics.snapshot_clients()
    fa = next(s for s in snapshots if s.name == "fighter_a")
    assert fa.sport == "MMA"
    assert fa.weight_kg == 75.0
    assert "creatine" in fa.current_supplements


def test_clients_by_sport(populated_practice):
    by_sport = team_analytics.clients_by_sport()
    assert "MMA" in by_sport
    assert len(by_sport["MMA"]) == 2
    assert "running" in by_sport
    assert len(by_sport["running"]) == 1


def test_supplement_frequency(populated_practice):
    freq = team_analytics.supplement_frequency()
    # creatine is in all 3 clients
    assert freq.get("creatine") == 3
    # beta-alanine only fighter_a
    assert freq.get("beta-alanine") == 1
    # omega_3 only fighter_b
    assert freq.get("omega_3") == 1


def test_incomplete_profiles(populated_practice):
    # Create a client with incomplete profile
    client_manager.create_client("incomplete_client", "")
    profile = {"sport": "boxing"}  # missing required fields
    p = client_manager.profile_path("incomplete_client")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(profile))

    incomplete = team_analytics.incomplete_profiles()
    assert "incomplete_client" in incomplete


def test_inactive_clients_all_new(populated_practice):
    # No memory files = all considered inactive
    stale = team_analytics.inactive_clients(days_threshold=30)
    assert "fighter_a" in stale
    assert "fighter_b" in stale
    assert "runner_a" in stale


def test_format_team_summary(populated_practice):
    summary = team_analytics.format_team_summary()
    assert "Practice summary" in summary
    assert "MMA" in summary
    assert "creatine" in summary
    assert "3 clients" in summary


def test_empty_practice(tmp_path, monkeypatch):
    monkeypatch.setattr(client_manager, "KIWI_DIR", tmp_path)
    monkeypatch.setattr(client_manager, "CLIENTS_DIR", tmp_path / "clients")
    monkeypatch.setattr(client_manager, "ACTIVE_CLIENT_FILE", tmp_path / "active_client.txt")
    monkeypatch.setattr(client_manager, "LEGACY_PROFILE", tmp_path / "profile.json")
    monkeypatch.setattr(client_manager, "LEGACY_MEMORY", tmp_path / "memory.json")
    monkeypatch.setattr(client_manager, "LEGACY_ARCHIVE", tmp_path / "episodic_archive.json")
    client_manager.ensure_setup()

    summary = team_analytics.format_team_summary()
    assert "No clients" in summary
