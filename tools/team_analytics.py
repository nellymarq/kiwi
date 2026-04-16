"""
Team Analytics — Cross-client aggregation for multi-athlete practice.

Aggregates data across all clients (excluding 'self' by default) to answer:
- "Show ferritin across all my athletes"
- "Which supplements am I recommending most?"
- "Whose profiles are incomplete?"
- "Who hasn't had research in >30 days?"

Read-only; no cross-client modifications.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from memory import client_manager


@dataclass
class ClientSnapshot:
    name: str
    sport: str
    age: int | None
    sex: str | None
    weight_kg: float | None
    current_supplements: list[str]
    last_research_ts: str | None
    profile_complete: bool


def _load_client_profile(client_name: str) -> dict[str, Any]:
    path = client_manager.profile_path(client_name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _load_client_memory(client_name: str) -> dict[str, Any]:
    path = client_manager.memory_path(client_name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def snapshot_clients(include_self: bool = False) -> list[ClientSnapshot]:
    """Return profile+memory snapshot for all clients."""
    snapshots = []
    for c in client_manager.list_clients():
        name = c["name"]
        if name == "self" and not include_self:
            continue
        profile = _load_client_profile(name)
        memory = _load_client_memory(name)

        episodic = memory.get("episodic", [])
        last_ts = episodic[-1].get("ts") if episodic else None

        snapshots.append(ClientSnapshot(
            name=name,
            sport=profile.get("sport", "") or "",
            age=profile.get("age"),
            sex=profile.get("sex"),
            weight_kg=profile.get("weight_kg"),
            current_supplements=profile.get("current_supplements", []) or [],
            last_research_ts=last_ts,
            profile_complete=bool(
                profile.get("weight_kg") and profile.get("sex")
                and profile.get("age") and profile.get("activity_level")
            ),
        ))
    return snapshots


def supplement_frequency() -> dict[str, int]:
    """Count how many clients are on each supplement across the practice."""
    counts: dict[str, int] = {}
    for s in snapshot_clients():
        for supp in s.current_supplements:
            key = supp.strip().lower()
            if key:
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def clients_by_sport() -> dict[str, list[str]]:
    """Group clients by sport."""
    by_sport: dict[str, list[str]] = {}
    for s in snapshot_clients():
        sport = s.sport or "unspecified"
        by_sport.setdefault(sport, []).append(s.name)
    return by_sport


def inactive_clients(days_threshold: int = 30) -> list[str]:
    """Clients with no research exchanges in >N days."""
    now = datetime.now(timezone.utc)
    stale = []
    for s in snapshot_clients():
        if not s.last_research_ts:
            stale.append(s.name)
            continue
        try:
            last = datetime.fromisoformat(s.last_research_ts.replace("Z", "+00:00"))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if (now - last).days > days_threshold:
                stale.append(s.name)
        except (ValueError, TypeError):
            stale.append(s.name)
    return stale


def incomplete_profiles() -> list[str]:
    """Clients with missing required profile fields."""
    return [s.name for s in snapshot_clients() if not s.profile_complete]


def format_team_summary() -> str:
    """Human-readable cross-client summary."""
    snapshots = snapshot_clients()
    if not snapshots:
        return "No clients yet. Add with /new_client <name>."

    lines = [f"Practice summary: {len(snapshots)} clients", ""]

    # By sport
    by_sport = clients_by_sport()
    lines.append("Clients by sport:")
    for sport, clients in sorted(by_sport.items()):
        lines.append(f"  {sport}: {len(clients)} — {', '.join(clients[:5])}" + ("..." if len(clients) > 5 else ""))

    # Top supplements
    supps = supplement_frequency()
    if supps:
        lines.append("")
        lines.append("Most-prescribed supplements:")
        for name, count in list(supps.items())[:10]:
            lines.append(f"  {name}: {count} client(s)")

    # Inactive
    stale = inactive_clients(30)
    if stale:
        lines.append("")
        lines.append(f"Inactive (no research in >30 days): {len(stale)}")
        lines.append(f"  {', '.join(stale[:10])}")

    # Incomplete profiles
    incomplete = incomplete_profiles()
    if incomplete:
        lines.append("")
        lines.append(f"Incomplete profiles: {len(incomplete)}")
        lines.append(f"  {', '.join(incomplete[:10])}")

    return "\n".join(lines)
