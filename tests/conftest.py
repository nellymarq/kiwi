"""Shared pytest fixtures for Kiwi tests.

Auto-loaded by pytest for every test under tests/. Fixtures here should
only be ones duplicated across ≥2 test files. Single-use fixtures belong
in the test file itself.
"""
import pytest

from memory import client_manager


@pytest.fixture
def clean_client(tmp_path, monkeypatch):
    """Isolated per-test client directory.

    Monkey-patches client_manager's 6 path constants to point inside
    tmp_path, runs ensure_setup, and creates a single client named
    'test_athlete'. Returns the client name.

    Used by memory-module tests (progress, profile, interventions,
    sessions, session_log, watch_list). test_preferences.py overrides
    this with its own local fixture returning 'test_client' because
    test bodies reference that literal.

    Fixture is per-test scoped; each test gets a fresh tmp_path + fresh
    monkey-patches (monkeypatch auto-reverts after each test).
    """
    monkeypatch.setattr(client_manager, "KIWI_DIR", tmp_path)
    monkeypatch.setattr(client_manager, "CLIENTS_DIR", tmp_path / "clients")
    monkeypatch.setattr(client_manager, "ACTIVE_CLIENT_FILE", tmp_path / "active_client.txt")
    monkeypatch.setattr(client_manager, "LEGACY_PROFILE", tmp_path / "profile.json")
    monkeypatch.setattr(client_manager, "LEGACY_MEMORY", tmp_path / "memory.json")
    monkeypatch.setattr(client_manager, "LEGACY_ARCHIVE", tmp_path / "episodic_archive.json")
    client_manager.ensure_setup()
    client_manager.create_client("test_athlete", "")
    return "test_athlete"
