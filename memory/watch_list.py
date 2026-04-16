"""
Watch List — Topic subscriptions for living reviews.

Per-client subscriptions to research topics. When /digest runs, Kiwi re-searches
each watched topic and highlights literature published since the last digest.

Storage: ~/.kiwi/clients/<name>/watch_list.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import client_manager


def _watch_path(client: str | None = None) -> Path:
    return client_manager.get_client_dir(client) / "watch_list.json"


class WatchList:
    """Per-client research topic subscriptions."""

    def __init__(self, client: str | None = None):
        self.client = client
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        path = _watch_path(self.client)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"topics": [], "last_digest_ts": None}

    def save(self):
        path = _watch_path(self.client)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.data, indent=2, default=str))

    def add(self, topic: str) -> bool:
        """Add a topic to the watch list. Returns False if already watched."""
        topic = topic.strip()
        if not topic:
            return False
        existing = [t["topic"].lower() for t in self.data.get("topics", [])]
        if topic.lower() in existing:
            return False
        self.data.setdefault("topics", []).append({
            "topic": topic,
            "added_ts": datetime.now(timezone.utc).isoformat(),
            "last_seen_dois": [],
        })
        self.save()
        return True

    def remove(self, topic: str) -> bool:
        """Remove a topic. Returns False if not found."""
        topic_lower = topic.strip().lower()
        topics = self.data.get("topics", [])
        new_topics = [t for t in topics if t["topic"].lower() != topic_lower]
        if len(new_topics) == len(topics):
            return False
        self.data["topics"] = new_topics
        self.save()
        return True

    def list_topics(self) -> list[dict]:
        return list(self.data.get("topics", []))

    def mark_digest_run(self, topic: str, seen_dois: list[str]):
        """Record DOIs seen during digest so we can detect new ones next time."""
        for t in self.data.get("topics", []):
            if t["topic"].lower() == topic.strip().lower():
                # Merge, dedupe, keep last 200 to limit storage
                combined = list(set((t.get("last_seen_dois", []) + seen_dois)))
                t["last_seen_dois"] = combined[-200:]
                t["last_digest_ts"] = datetime.now(timezone.utc).isoformat()
                break
        self.save()

    def update_global_digest_ts(self):
        self.data["last_digest_ts"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def get_last_seen(self, topic: str) -> set[str]:
        """Return the set of DOIs previously seen for a topic (lowercased)."""
        for t in self.data.get("topics", []):
            if t["topic"].lower() == topic.strip().lower():
                return {d.lower() for d in t.get("last_seen_dois", [])}
        return set()
