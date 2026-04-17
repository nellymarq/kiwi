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


def compare_clients(name_a: str, name_b: str) -> str:
    """Side-by-side comparison of two clients' profiles and latest biomarkers."""
    prof_a = _load_client_profile(name_a)
    prof_b = _load_client_profile(name_b)

    if not prof_a and not prof_b:
        return f"Neither '{name_a}' nor '{name_b}' found."
    if not prof_a:
        return f"Client '{name_a}' not found."
    if not prof_b:
        return f"Client '{name_b}' not found."

    # Profile comparison
    fields = ["sport", "age", "sex", "weight_kg", "height_cm", "body_fat_pct",
              "training_status", "activity_level", "primary_goal"]

    lines = [f"{'Field':<20} {name_a:<20} {name_b:<20}", "-" * 60]
    for f in fields:
        va = str(prof_a.get(f, "—"))
        vb = str(prof_b.get(f, "—"))
        lines.append(f"{f:<20} {va:<20} {vb:<20}")

    # Supplement stacks
    supps_a = prof_a.get("current_supplements", []) or []
    supps_b = prof_b.get("current_supplements", []) or []
    lines.append("")
    lines.append(f"{'Supplements':<20} {', '.join(supps_a) or '—':<20}")
    lines.append(f"{'':<20} {', '.join(supps_b) or '—':<20}")

    # Latest biomarkers from progress data
    from memory.progress import ProgressTracker
    pt_a = ProgressTracker(client=name_a)
    pt_b = ProgressTracker(client=name_b)
    all_metrics = sorted(set(pt_a.get_all_metrics() + pt_b.get_all_metrics()))

    if all_metrics:
        lines.append("")
        lines.append(f"{'Biomarker':<20} {name_a:<20} {name_b:<20}")
        lines.append("-" * 60)
        for m in all_metrics:
            la = pt_a.get_latest(m)
            lb = pt_b.get_latest(m)
            va = f"{la['value']:.1f} {la.get('unit', '')}" if la else "—"
            vb = f"{lb['value']:.1f} {lb.get('unit', '')}" if lb else "—"
            lines.append(f"{m:<20} {va:<20} {vb:<20}")

    return "\n".join(lines)


def format_client_snapshot(client_name: str) -> str:
    """Complete snapshot of a single client — profile, biomarkers, stack, progress."""
    profile = _load_client_profile(client_name)
    memory = _load_client_memory(client_name)

    if not profile and not memory:
        return f"Client '{client_name}' has no data. Run /onboard."

    lines = [f"Client Snapshot: {client_name}", "=" * 40, ""]

    # Profile
    if profile:
        lines.append("Profile:")
        for key in ["name", "age", "sex", "weight_kg", "height_cm", "body_fat_pct",
                     "sport", "training_status", "activity_level", "primary_goal"]:
            val = profile.get(key)
            if val:
                lines.append(f"  {key}: {val}")
        supps = profile.get("current_supplements", [])
        if supps:
            lines.append(f"  supplements: {', '.join(supps)}")
        restrictions = profile.get("dietary_restrictions", [])
        if restrictions:
            lines.append(f"  restrictions: {', '.join(restrictions)}")
        conditions = profile.get("health_conditions", [])
        if conditions:
            lines.append(f"  conditions: {', '.join(conditions)}")
    else:
        lines.append("Profile: not set (run /onboard)")

    # Latest biomarkers from progress
    from memory.progress import ProgressTracker
    pt = ProgressTracker(client=client_name)
    metrics = pt.get_all_metrics()
    if metrics:
        lines.append("")
        lines.append("Latest Biomarkers:")
        for m in metrics:
            latest = pt.get_latest(m)
            if latest:
                lines.append(f"  {m}: {latest['value']:.1f} {latest.get('unit', '')} ({latest.get('ts', '')[:10]})")

    # Active interventions
    from memory.interventions import InterventionTracker
    it = InterventionTracker(client=client_name)
    active = it.list_active()
    if active:
        lines.append("")
        lines.append("Active Interventions:")
        for e in active:
            dose = f" ({e['dose']})" if e.get("dose") else ""
            lines.append(f"  {e['name']}{dose} — since {e['started_at'][:10]}")

    # Recent research
    episodic = memory.get("episodic", []) if memory else []
    if episodic:
        lines.append("")
        lines.append("Recent Research:")
        for e in episodic[-5:]:
            score = e.get("quality_score", "?")
            lines.append(f"  [{e.get('ts', '')[:10]}] (score: {score}) {e.get('query', '')[:100]}")

    # Stats
    lines.append("")
    total_queries = memory.get("total_queries", 0) if memory else 0
    sessions = memory.get("session_count", 0) if memory else 0
    lines.append(f"Total queries: {total_queries} · Sessions: {sessions}")

    return "\n".join(lines)
