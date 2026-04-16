"""Tests for research topic watch list."""

import pytest
from pathlib import Path
from memory import client_manager
from memory.watch_list import WatchList


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


def test_watch_list_starts_empty(clean_client):
    wl = WatchList(client=clean_client)
    assert wl.list_topics() == []


def test_add_topic(clean_client):
    wl = WatchList(client=clean_client)
    assert wl.add("creatine loading")
    topics = wl.list_topics()
    assert len(topics) == 1
    assert topics[0]["topic"] == "creatine loading"


def test_add_duplicate_returns_false(clean_client):
    wl = WatchList(client=clean_client)
    wl.add("creatine")
    assert not wl.add("creatine")
    assert not wl.add("CREATINE")  # case-insensitive
    assert len(wl.list_topics()) == 1


def test_remove_topic(clean_client):
    wl = WatchList(client=clean_client)
    wl.add("topic A")
    wl.add("topic B")
    assert wl.remove("topic A")
    assert [t["topic"] for t in wl.list_topics()] == ["topic B"]


def test_remove_nonexistent(clean_client):
    wl = WatchList(client=clean_client)
    assert not wl.remove("ghost topic")


def test_persistence(clean_client):
    wl1 = WatchList(client=clean_client)
    wl1.add("topic 1")
    wl1.add("topic 2")

    wl2 = WatchList(client=clean_client)
    assert len(wl2.list_topics()) == 2


def test_mark_digest_run(clean_client):
    wl = WatchList(client=clean_client)
    wl.add("creatine")
    wl.mark_digest_run("creatine", ["10.1/a", "10.1/b"])
    seen = wl.get_last_seen("creatine")
    assert "10.1/a" in seen
    assert "10.1/b" in seen


def test_get_last_seen_empty(clean_client):
    wl = WatchList(client=clean_client)
    wl.add("topic")
    assert wl.get_last_seen("topic") == set()


def test_mark_digest_dedupe(clean_client):
    wl = WatchList(client=clean_client)
    wl.add("topic")
    wl.mark_digest_run("topic", ["10.1/a"])
    wl.mark_digest_run("topic", ["10.1/a", "10.1/b"])
    seen = wl.get_last_seen("topic")
    assert len(seen) == 2


def test_per_client_isolation(clean_client):
    client_manager.create_client("other", "")
    wl_a = WatchList(client=clean_client)
    wl_a.add("topic for A")

    wl_b = WatchList(client="other")
    assert len(wl_b.list_topics()) == 0


def test_empty_topic_not_added(clean_client):
    wl = WatchList(client=clean_client)
    assert not wl.add("")
    assert not wl.add("   ")
