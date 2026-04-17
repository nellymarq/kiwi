"""
Structured Session Log — Per-client query history for retrospective analysis.

Each research exchange is logged with: timestamp, query, route (research/quick/memory),
score, thread, cost estimate. Stored as JSONL for streaming append.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import client_manager


def _log_path(client: str | None = None) -> Path:
    d = client_manager.get_client_dir(client)
    d.mkdir(parents=True, exist_ok=True)
    return d / "session_log.jsonl"


def log_exchange(
    query: str,
    route: str,
    score: float | None = None,
    thread: str | None = None,
    cost_usd: float = 0.0,
    client: str | None = None,
):
    """Append a structured log entry for a single exchange."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "query": query[:500],
        "route": route,
    }
    if score is not None:
        entry["score"] = round(score, 3)
    if thread:
        entry["thread"] = thread
    if cost_usd > 0:
        entry["cost_usd"] = round(cost_usd, 6)

    path = _log_path(client)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_log(client: str | None = None, limit: int = 50) -> list[dict]:
    """Read the most recent N log entries."""
    path = _log_path(client)
    if not path.exists():
        return []
    entries = []
    try:
        for line in path.read_text().splitlines():
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries[-limit:]


def log_stats(client: str | None = None) -> dict:
    """Summary statistics from the log."""
    entries = read_log(client, limit=10000)
    if not entries:
        return {"total_queries": 0}

    routes = {}
    total_cost = 0.0
    scores = []
    for e in entries:
        route = e.get("route", "unknown")
        routes[route] = routes.get(route, 0) + 1
        total_cost += e.get("cost_usd", 0.0)
        if "score" in e:
            scores.append(e["score"])

    return {
        "total_queries": len(entries),
        "by_route": routes,
        "total_cost_usd": round(total_cost, 4),
        "avg_score": round(sum(scores) / len(scores), 3) if scores else None,
        "first_query": entries[0].get("ts", "")[:10] if entries else None,
        "last_query": entries[-1].get("ts", "")[:10] if entries else None,
    }
