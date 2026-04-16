"""Tests for the multi-client manager."""

import json
import pytest
from pathlib import Path

from memory import client_manager


@pytest.fixture
def clean_kiwi_dir(tmp_path, monkeypatch):
    """Isolated kiwi dir for each test."""
    monkeypatch.setattr(client_manager, "KIWI_DIR", tmp_path)
    monkeypatch.setattr(client_manager, "CLIENTS_DIR", tmp_path / "clients")
    monkeypatch.setattr(client_manager, "ACTIVE_CLIENT_FILE", tmp_path / "active_client.txt")
    monkeypatch.setattr(client_manager, "LEGACY_PROFILE", tmp_path / "profile.json")
    monkeypatch.setattr(client_manager, "LEGACY_MEMORY", tmp_path / "memory.json")
    monkeypatch.setattr(client_manager, "LEGACY_ARCHIVE", tmp_path / "episodic_archive.json")
    return tmp_path


def test_ensure_setup_creates_defaults(clean_kiwi_dir):
    client_manager.ensure_setup()
    assert (clean_kiwi_dir / "clients").is_dir()
    assert (clean_kiwi_dir / "clients" / "self").is_dir()
    assert client_manager.get_active_client() == "self"


def test_legacy_migration(clean_kiwi_dir):
    (clean_kiwi_dir / "profile.json").write_text('{"name": "Nelson"}')
    (clean_kiwi_dir / "memory.json").write_text('{"episodic": []}')
    client_manager.ensure_setup()
    self_dir = clean_kiwi_dir / "clients" / "self"
    migrated_profile = self_dir / "profile.json"
    assert migrated_profile.exists()
    assert json.loads(migrated_profile.read_text())["name"] == "Nelson"


def test_create_client(clean_kiwi_dir):
    ok, msg = client_manager.create_client("fighter_one", "UFC welterweight")
    assert ok
    assert "fighter_one" in msg
    assert (clean_kiwi_dir / "clients" / "fighter_one").is_dir()
    desc = (clean_kiwi_dir / "clients" / "fighter_one" / "description.txt").read_text()
    assert "UFC welterweight" in desc


def test_create_client_invalid_name(clean_kiwi_dir):
    ok, msg = client_manager.create_client("Has Spaces!", "")
    # Should normalize to "has_spaces!" which still fails validation
    assert not ok
    assert "1-40 chars" in msg


def test_create_client_duplicate(clean_kiwi_dir):
    client_manager.create_client("athlete_a", "")
    ok, msg = client_manager.create_client("athlete_a", "")
    assert not ok
    assert "already exists" in msg


def test_switch_client(clean_kiwi_dir):
    client_manager.create_client("athlete_a", "")
    assert client_manager.set_active_client("athlete_a")
    assert client_manager.get_active_client() == "athlete_a"


def test_switch_client_nonexistent(clean_kiwi_dir):
    assert not client_manager.set_active_client("ghost")


def test_delete_client(clean_kiwi_dir):
    client_manager.create_client("temp_client", "")
    ok, msg = client_manager.delete_client("temp_client")
    assert ok
    assert not (clean_kiwi_dir / "clients" / "temp_client").exists()


def test_cannot_delete_self(clean_kiwi_dir):
    client_manager.ensure_setup()
    ok, msg = client_manager.delete_client("self")
    assert not ok
    assert "default" in msg.lower()


def test_cannot_delete_active_client(clean_kiwi_dir):
    client_manager.create_client("athlete_b", "")
    client_manager.set_active_client("athlete_b")
    ok, msg = client_manager.delete_client("athlete_b")
    assert not ok
    assert "active" in msg.lower()


def test_list_clients(clean_kiwi_dir):
    client_manager.create_client("alice", "runner")
    client_manager.create_client("bob", "lifter")
    clients = client_manager.list_clients()
    names = [c["name"] for c in clients]
    assert "self" in names
    assert "alice" in names
    assert "bob" in names
    self_entry = next(c for c in clients if c["name"] == "self")
    assert self_entry["is_active"]


def test_profile_per_client(clean_kiwi_dir, monkeypatch):
    from memory.profile import UserProfile
    client_manager.create_client("alice", "")
    client_manager.create_client("bob", "")

    alice_profile = UserProfile(client="alice")
    alice_profile.set("weight_kg", "60")
    alice_profile.save()

    bob_profile = UserProfile(client="bob")
    bob_profile.set("weight_kg", "90")
    bob_profile.save()

    # Reload each to verify isolation
    alice_reload = UserProfile(client="alice")
    bob_reload = UserProfile(client="bob")
    assert alice_reload.get("weight_kg") == 60.0
    assert bob_reload.get("weight_kg") == 90.0
