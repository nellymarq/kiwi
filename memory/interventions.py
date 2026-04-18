"""
Intervention Tracker — Link supplement/protocol starts to biomarker outcomes.

Stores interventions with start date, then correlates against progress data
to assess whether the intervention produced the expected effect.

Storage: ~/.kiwi/clients/<name>/interventions.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from . import client_manager
from .progress import ProgressTracker


def _interventions_path(client: str | None = None) -> Path:
    d = client_manager.get_client_dir(client)
    d.mkdir(parents=True, exist_ok=True)
    return d / "interventions.json"


class InterventionTracker:
    """Per-client intervention tracking with outcome correlation."""

    def __init__(self, client: str | None = None):
        self.client = client
        self.data: list[dict] = self._load()

    def _load(self) -> list[dict]:
        path = _interventions_path(self.client)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def save(self):
        path = _interventions_path(self.client)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.data, indent=2, default=str))

    def start(self, name: str, dose: str = "", target_metric: str = "", note: str = "") -> dict:
        """Record the start of an intervention."""
        entry = {
            "name": name.strip(),
            "dose": dose.strip(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "stopped_at": None,
            "target_metric": target_metric.strip().lower().replace(" ", "_"),
            "note": note[:300],
            "status": "active",
        }
        self.data.append(entry)
        self.save()
        return entry

    def stop(self, name: str, reason: str = "") -> bool:
        """Mark an intervention as stopped. Returns False if not found."""
        name_lower = name.strip().lower()
        for entry in reversed(self.data):
            if entry["name"].lower() == name_lower and entry["status"] == "active":
                entry["stopped_at"] = datetime.now(timezone.utc).isoformat()
                entry["status"] = "stopped"
                if reason:
                    entry["stop_reason"] = reason[:300]
                self.save()
                return True
        return False

    def list_active(self) -> list[dict]:
        return [e for e in self.data if e["status"] == "active"]

    def list_all(self) -> list[dict]:
        return list(self.data)

    def check_outcome(self, name: str) -> dict:
        """
        Correlate an intervention with its target metric's progress data.
        Returns before/after values if target_metric has data.
        """
        name_lower = name.strip().lower()
        entry = None
        for e in reversed(self.data):
            if e["name"].lower() == name_lower:
                entry = e
                break
        if not entry:
            return {"error": f"Intervention '{name}' not found"}

        target = entry.get("target_metric", "")
        if not target:
            return {
                "intervention": entry["name"],
                "status": entry["status"],
                "started": entry["started_at"][:10],
                "message": "No target metric specified. Use /intervention start <name> <dose> <target_metric>",
            }

        started_at = entry["started_at"]
        progress = ProgressTracker(client=self.client)
        history = progress.get_history(target, limit=100)

        if not history:
            return {
                "intervention": entry["name"],
                "target_metric": target,
                "message": f"No progress data for '{target}'. Track with /track {target} <value>",
            }

        # Split into before and after intervention start
        before = [h for h in history if h["ts"] < started_at]
        after = [h for h in history if h["ts"] >= started_at]

        result = {
            "intervention": entry["name"],
            "dose": entry.get("dose", ""),
            "target_metric": target,
            "status": entry["status"],
            "started": started_at[:10],
            "stopped": entry.get("stopped_at", "")[:10] if entry.get("stopped_at") else "ongoing",
        }

        if before:
            before_vals = [h["value"] for h in before]
            result["baseline_avg"] = round(sum(before_vals) / len(before_vals), 2)
            result["baseline_last"] = before_vals[-1]
            result["baseline_n"] = len(before_vals)

        if after:
            after_vals = [h["value"] for h in after]
            result["post_avg"] = round(sum(after_vals) / len(after_vals), 2)
            result["post_last"] = after_vals[-1]
            result["post_n"] = len(after_vals)

        if before and after:
            before_avg = result["baseline_avg"]
            after_avg = result["post_avg"]
            change = after_avg - before_avg
            pct = (change / before_avg * 100) if before_avg != 0 else 0
            unit = history[0].get("unit", "")
            direction = "↑" if change > 0 else "↓" if change < 0 else "→"
            result["change"] = round(change, 2)
            result["change_pct"] = round(pct, 1)
            result["direction"] = direction
            result["unit"] = unit
            result["assessment"] = (
                f"{target} changed {direction} {abs(change):.1f} {unit} ({pct:+.1f}%) "
                f"since starting {entry['name']}"
            )

        return result

    def format_active(self) -> str:
        active = self.list_active()
        if not active:
            return "No active interventions. Start one with /intervention start <name> [dose] [target_metric]"
        lines = ["Active interventions:", ""]
        for e in active:
            started = e["started_at"][:10]
            dose = f" ({e['dose']})" if e.get("dose") else ""
            target = f" → tracking {e['target_metric']}" if e.get("target_metric") else ""
            lines.append(f"  • {e['name']}{dose} — since {started}{target}")
        return "\n".join(lines)

    def format_outcome(self, result: dict) -> str:
        if "error" in result:
            return result["error"]
        if "message" in result and "change" not in result:
            return result["message"]

        lines = [
            f"Intervention: {result['intervention']}",
            f"Dose: {result.get('dose', 'not specified')}",
            f"Status: {result['status']} (started {result['started']}, {result.get('stopped', 'ongoing')})",
            f"Target: {result['target_metric']}",
        ]
        if "baseline_avg" in result:
            lines.append(f"Baseline: {result['baseline_avg']} {result.get('unit', '')} (n={result['baseline_n']})")
        if "post_avg" in result:
            lines.append(f"Post-intervention: {result['post_avg']} {result.get('unit', '')} (n={result['post_n']})")
        if "assessment" in result:
            lines.append(f"")
            lines.append(f"Result: {result['assessment']}")
        return "\n".join(lines)

    # Standard retest intervals by metric (weeks)
    RETEST_INTERVALS: dict[str, int] = {
        "ferritin": 6, "hemoglobin": 6, "vitamin_d": 8,
        "testosterone": 8, "cortisol": 4, "tsh": 8,
        "free_t3": 8, "free_t4": 8, "hba1c": 12,
        "ldl": 8, "hdl": 8, "triglycerides": 8,
        "homocysteine": 8, "crp": 6, "fasting_insulin": 8,
        "dhea_s": 12, "estradiol": 4, "progesterone": 4,
    }

    def retest_due(self) -> list[dict]:
        """Check which interventions have target metrics due for retest."""
        now = datetime.now(timezone.utc)
        due = []
        for entry in self.data:
            if entry["status"] != "active":
                continue
            target = entry.get("target_metric", "")
            if not target:
                continue
            started = entry.get("started_at", "")
            if not started:
                continue
            try:
                start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
            interval_weeks = self.RETEST_INTERVALS.get(target, 6)
            retest_date = start_dt + timedelta(weeks=interval_weeks)
            if now >= retest_date:
                weeks_overdue = int((now - retest_date).days / 7)
                due.append({
                    "intervention": entry["name"],
                    "target_metric": target,
                    "started": started[:10],
                    "retest_after": retest_date.strftime("%Y-%m-%d"),
                    "weeks_overdue": weeks_overdue,
                    "status": "OVERDUE" if weeks_overdue > 0 else "DUE NOW",
                })
        return due

    def format_retest_due(self) -> str:
        """Format retest-due items for display."""
        due = self.retest_due()
        if not due:
            return "No biomarkers due for retest."
        lines = ["Biomarker Retests Due:", ""]
        for d in due:
            icon = "🔴" if d["weeks_overdue"] > 2 else "🟡" if d["weeks_overdue"] > 0 else "🟢"
            lines.append(
                f"  {icon} {d['target_metric']} — for {d['intervention']} "
                f"(started {d['started']}, retest after {d['retest_after']}, "
                f"{d['status']})"
            )
        return "\n".join(lines)
