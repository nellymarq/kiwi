"""Tests for preference tracking."""

import json
import pytest
from pathlib import Path

from memory import client_manager
from memory.preferences import PreferencesStore


@pytest.fixture
def clean_client(tmp_path, monkeypatch):
    """Isolated client directory."""
    monkeypatch.setattr(client_manager, "KIWI_DIR", tmp_path)
    monkeypatch.setattr(client_manager, "CLIENTS_DIR", tmp_path / "clients")
    monkeypatch.setattr(client_manager, "ACTIVE_CLIENT_FILE", tmp_path / "active_client.txt")
    monkeypatch.setattr(client_manager, "LEGACY_PROFILE", tmp_path / "profile.json")
    monkeypatch.setattr(client_manager, "LEGACY_MEMORY", tmp_path / "memory.json")
    monkeypatch.setattr(client_manager, "LEGACY_ARCHIVE", tmp_path / "episodic_archive.json")
    client_manager.ensure_setup()
    client_manager.create_client("test_client", "")
    return "test_client"


def test_preferences_initialize_empty(clean_client):
    store = PreferencesStore(client=clean_client)
    assert store.data["accepted"] == []
    assert store.data["rejected"] == []


def test_record_accepted(clean_client):
    store = PreferencesStore(client=clean_client)
    store.record_accepted("Creatine 5g/d post-workout", note="Worked well")
    assert len(store.data["accepted"]) == 1
    assert store.data["accepted"][0]["note"] == "Worked well"


def test_record_rejected(clean_client):
    store = PreferencesStore(client=clean_client)
    store.record_rejected("Vitamin C 5g/d", reason="Blunts training adaptation")
    assert len(store.data["rejected"]) == 1
    assert "adaptation" in store.data["rejected"][0]["reason"]


def test_preferences_persist(clean_client):
    store1 = PreferencesStore(client=clean_client)
    store1.record_accepted("Rec 1")
    store1.record_rejected("Rec 2")

    store2 = PreferencesStore(client=clean_client)
    assert len(store2.data["accepted"]) == 1
    assert len(store2.data["rejected"]) == 1


def test_stats(clean_client):
    store = PreferencesStore(client=clean_client)
    store.record_accepted("A")
    store.record_accepted("B")
    store.record_rejected("C")
    stats = store.stats()
    assert stats["total_accepted"] == 2
    assert stats["total_rejected"] == 1


def test_to_context_block_empty(clean_client):
    store = PreferencesStore(client=clean_client)
    assert store.to_context_block() == ""


def test_to_context_block_with_data(clean_client):
    store = PreferencesStore(client=clean_client)
    store.record_accepted("Creatine 5g/d post-workout", note="Improved 1RM by 8%")
    store.record_rejected("High-dose vitamin C for endurance", reason="Blunts mitochondrial adaptation")

    block = store.to_context_block()
    assert "Creatine" in block
    assert "✓" in block
    assert "✗" in block
    assert "adaptation" in block


def test_recent_accepted_limit(clean_client):
    store = PreferencesStore(client=clean_client)
    for i in range(10):
        store.record_accepted(f"Recommendation {i}")
    recent = store.recent_accepted(n=3)
    assert len(recent) == 3
    assert recent[-1]["recommendation"] == "Recommendation 9"


def test_per_client_isolation(clean_client):
    # clean_client already created test_client
    client_manager.create_client("other_client", "")

    store_a = PreferencesStore(client="test_client")
    store_a.record_accepted("Rec for test_client")

    store_b = PreferencesStore(client="other_client")
    assert len(store_b.data["accepted"]) == 0
