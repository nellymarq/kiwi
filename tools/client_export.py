"""
Client Export — Dump everything about a client to a portable folder.

Creates a timestamped directory with: profile, progress, interventions,
preferences, research log, and a summary README.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from memory import client_manager
from memory.progress import ProgressTracker
from memory.interventions import InterventionTracker
from memory.preferences import PreferencesStore
from memory.session_log import read_log


EXPORT_BASE = Path.home() / ".kiwi" / "client_exports"


def export_client(client_name: str) -> Path:
    """Export all client data to a portable directory. Returns export path."""
    EXPORT_BASE.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = EXPORT_BASE / f"{client_name}_{ts}"
    export_dir.mkdir(parents=True, exist_ok=True)

    client_dir = client_manager.get_client_dir(client_name)

    # Copy raw data files
    for filename in ["profile.json", "memory.json", "progress.jsonl",
                     "interventions.json", "preferences.json",
                     "watch_list.json", "session_log.jsonl"]:
        src = client_dir / filename
        if src.exists():
            shutil.copy2(src, export_dir / filename)

    # Copy sessions directory
    sessions_dir = client_dir / "sessions"
    if sessions_dir.exists():
        dest_sessions = export_dir / "sessions"
        dest_sessions.mkdir(exist_ok=True)
        for f in sessions_dir.glob("*.json"):
            shutil.copy2(f, dest_sessions / f.name)

    # Generate summary README
    _write_summary(client_name, export_dir)

    return export_dir


def _write_summary(client_name: str, export_dir: Path):
    """Write a human-readable summary of the export."""
    profile_path = export_dir / "profile.json"
    profile = {}
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text())
        except json.JSONDecodeError:
            pass

    lines = [
        f"# Client Export: {client_name}",
        f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Profile",
    ]
    for key, val in profile.items():
        lines.append(f"- {key}: {val}")

    # Progress summary
    pt = ProgressTracker(client=client_name)
    metrics = pt.get_all_metrics()
    if metrics:
        lines.append("")
        lines.append("## Latest Metrics")
        for m in metrics:
            latest = pt.get_latest(m)
            if latest:
                lines.append(f"- {m}: {latest['value']} {latest.get('unit', '')} ({latest.get('ts', '')[:10]})")

    # Interventions
    it = InterventionTracker(client=client_name)
    active = it.list_active()
    all_interventions = it.list_all()
    if all_interventions:
        lines.append("")
        lines.append(f"## Interventions ({len(active)} active, {len(all_interventions)} total)")
        for e in all_interventions[-10:]:
            status = e.get("status", "?")
            lines.append(f"- {e['name']} ({status}) — started {e.get('started_at', '')[:10]}")

    # Research log stats
    log_entries = read_log(client=client_name, limit=1000)
    if log_entries:
        lines.append("")
        lines.append(f"## Research Log ({len(log_entries)} queries)")
        lines.append(f"- First: {log_entries[0].get('ts', '')[:10]}")
        lines.append(f"- Last: {log_entries[-1].get('ts', '')[:10]}")

    # Files included
    lines.append("")
    lines.append("## Files Included")
    for f in sorted(export_dir.rglob("*")):
        if f.is_file() and f.name != "README.md":
            lines.append(f"- {f.relative_to(export_dir)}")

    (export_dir / "README.md").write_text("\n".join(lines))
