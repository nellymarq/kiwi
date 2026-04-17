"""Tests for structured session logging."""

import json
import pytest
from pathlib import Path
from memory import client_manager
from memory.session_log import log_exchange, read_log, log_stats


@pytest.fixture
def clean_client(tmp_path, monkeypatch):
    monkeypatch.setattr(client_manager, "KIWI_DIR", tmp_path)
    monkeypatch.setattr(client_manager, "CLIENTS_DIR", tmp_path / "clients")
    monkeypatch.setattr(client_manager, "ACTIVE_CLIENT_FILE", tmp_path / "active_client.txt")
    monkeypatch.setattr(client_manager, "LEGACY_PROFILE", tmp_path / "profile.json")
    monkeypatch.setattr(client_manager, "LEGACY_MEMORY", tmp_path / "memory.json")
    monkeypatch.setattr(client_manager, "LEGACY_ARCHIVE", tmp_path / "episodic_archive.json")
    client_manager.ensure_setup()
    client_manager.create_client("test_athlete", "")
    return "test_athlete"


def test_log_and_read(clean_client):
    log_exchange("creatine timing", "research", score=0.85, client=clean_client)
    entries = read_log(client=clean_client)
    assert len(entries) == 1
    assert entries[0]["query"] == "creatine timing"
    assert entries[0]["route"] == "research"
    assert entries[0]["score"] == 0.85


def test_multiple_entries(clean_client):
    log_exchange("q1", "research", score=0.9, client=clean_client)
    log_exchange("q2", "quick", client=clean_client)
    log_exchange("q3", "memory", client=clean_client)
    entries = read_log(client=clean_client)
    assert len(entries) == 3


def test_stats(clean_client):
    log_exchange("q1", "research", score=0.8, cost_usd=0.05, client=clean_client)
    log_exchange("q2", "research", score=0.9, cost_usd=0.03, client=clean_client)
    log_exchange("q3", "quick", client=clean_client)

    stats = log_stats(client=clean_client)
    assert stats["total_queries"] == 3
    assert stats["by_route"]["research"] == 2
    assert stats["by_route"]["quick"] == 1
    assert stats["avg_score"] == 0.85
    assert stats["total_cost_usd"] == 0.08


def test_empty_log(clean_client):
    entries = read_log(client=clean_client)
    assert entries == []
    stats = log_stats(client=clean_client)
    assert stats["total_queries"] == 0


def test_cost_tracking(clean_client):
    log_exchange("expensive query", "research", cost_usd=0.15, client=clean_client)
    stats = log_stats(client=clean_client)
    assert stats["total_cost_usd"] == 0.15
